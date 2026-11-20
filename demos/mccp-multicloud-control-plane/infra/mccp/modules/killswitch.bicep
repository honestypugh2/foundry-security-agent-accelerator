// Automated kill switch:
//   scheduled query alert (tokens per agent per hour) ─┐
//   Datadog monitor webhook (datadog/*.json) ───────────┼─> Logic App (system MI) ─> ARM PUT APIM named value killed-agents
//   Consumption budget 80/100% ─> action group ─────────┘   (budget alerts carry no agent dimension: email only, no kill)
param location string
param apimName string
param logicAppName string
param actionGroupName string
param alertEmail string
param appInsightsId string
param budgetAmount int
param budgetStartDate string
param perAgentHourlyTokenKillThreshold int

var apimServiceContributorRoleId = '312a565d-c81f-4fd8-895a-4e21e48d571c'
var armApiVersion = '2024-05-01'

resource apim 'Microsoft.ApiManagement/service@2024-05-01' existing = {
  name: apimName
}

// ARM endpoints for the named value (public cloud). A GET does not return a named value's value
// (ARM reference: "This property will not be filled on 'GET' operations"), so the Logic App reads it with
// POST .../listValue, which returns {"value": "..."}.
var armEndpoint = environment().resourceManager
var namedValueUrl = '${armEndpoint}${substring(apim.id, 1)}/namedValues/killed-agents?api-version=${armApiVersion}'
var namedValueReadUrl = '${armEndpoint}${substring(apim.id, 1)}/namedValues/killed-agents/listValue?api-version=${armApiVersion}'

resource logicApp 'Microsoft.Logic/workflows@2019-05-01' = {
  name: logicAppName
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    state: 'Enabled'
    definition: {
      '$schema': 'https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#'
      contentVersion: '1.0.0.0'
      triggers: {
        manual: {
          type: 'Request'
          kind: 'Http'
          inputs: { schema: {} }
        }
      }
      actions: {
        // Azure Monitor common alert schema: data.alertContext.condition.allOf[0].dimensions[{name:'agent', value}]
        Filter_dimensions: {
          type: 'Query'
          runAfter: {}
          inputs: {
            from: '@coalesce(triggerBody()?[\'data\']?[\'alertContext\']?[\'condition\']?[\'allOf\']?[0]?[\'dimensions\'], json(\'[]\'))'
            where: '@equals(item()?[\'name\'], \'agent\')'
          }
        }
        // Datadog webhook: {"agent_id": "...", "alert_scope": "gen_ai.agent.id:<id>"}  (VALIDATE scope format)
        Compose_agent: {
          type: 'Compose'
          runAfter: { Filter_dimensions: [ 'Succeeded' ] }
          inputs: '@coalesce(triggerBody()?[\'agent_id\'], first(body(\'Filter_dimensions\'))?[\'value\'], last(split(coalesce(triggerBody()?[\'alert_scope\'], \'\'), \':\')))'
        }
        Has_agent: {
          type: 'If'
          runAfter: { Compose_agent: [ 'Succeeded' ] }
          expression: {
            and: [ { not: { equals: [ '@coalesce(outputs(\'Compose_agent\'), \'\')', '' ] } } ]
          }
          actions: {
            Get_killed_agents: {
              type: 'Http'
              runAfter: {}
              inputs: {
                method: 'POST'
                uri: namedValueReadUrl
                authentication: {
                  type: 'ManagedServiceIdentity'
                  audience: armEndpoint
                }
              }
            }
            Compose_new_value: {
              type: 'Compose'
              runAfter: { Get_killed_agents: [ 'Succeeded' ] }
              inputs: '@if(equals(body(\'Get_killed_agents\')?[\'value\'], \'none\'), outputs(\'Compose_agent\'), if(contains(split(body(\'Get_killed_agents\')?[\'value\'], \',\'), outputs(\'Compose_agent\')), body(\'Get_killed_agents\')?[\'value\'], concat(body(\'Get_killed_agents\')?[\'value\'], \',\', outputs(\'Compose_agent\'))))'
            }
            Put_killed_agents: {
              type: 'Http'
              runAfter: { Compose_new_value: [ 'Succeeded' ] }
              inputs: {
                method: 'PUT'
                uri: namedValueUrl
                headers: { 'Content-Type': 'application/json' }
                body: {
                  properties: {
                    displayName: 'killed-agents'
                    value: '@{outputs(\'Compose_new_value\')}'
                    secret: false
                  }
                }
                authentication: {
                  type: 'ManagedServiceIdentity'
                  audience: armEndpoint
                }
              }
            }
          }
          else: { actions: {} }
        }
      }
      outputs: {}
    }
  }
}

resource logicAppApimContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(apim.id, logicApp.id, apimServiceContributorRoleId)
  scope: apim
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', apimServiceContributorRoleId)
    principalId: logicApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: actionGroupName
  location: 'global'
  properties: {
    groupShortName: 'mccpkill'
    enabled: true
    emailReceivers: [
      { name: 'platform-owner', emailAddress: alertEmail, useCommonAlertSchema: true }
    ]
    logicAppReceivers: [
      {
        name: 'killswitch-logicapp'
        resourceId: logicApp.id
        callbackUrl: listCallbackUrl('${logicApp.id}/triggers/manual', '2019-05-01').value
        useCommonAlertSchema: true
      }
    ]
  }
}

resource runawayAlert 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = {
  name: 'mccp-agent-token-runaway'
  location: location
  properties: {
    displayName: 'mccp: agent token runaway (auto kill)'
    description: 'Fires per agent when hourly tokens exceed the threshold; the Logic App adds the agent to killed-agents.'
    severity: 1
    enabled: true
    evaluationFrequency: 'PT5M'
    windowSize: 'PT1H'
    scopes: [ appInsightsId ]
    criteria: {
      allOf: [
        {
          query: loadTextContent('../kql/budget_breach_alert.kql')
          timeAggregation: 'Total'
          metricMeasureColumn: 'TotalTokens'
          dimensions: [
            { name: 'agent', operator: 'Include', values: [ '*' ] }
          ]
          operator: 'GreaterThan'
          threshold: perAgentHourlyTokenKillThreshold
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    autoMitigate: false
    actions: {
      actionGroups: [ actionGroup.id ]
    }
  }
}

resource budget 'Microsoft.Consumption/budgets@2023-11-01' = {
  name: 'mccp-monthly-budget'
  properties: {
    category: 'Cost'
    amount: budgetAmount
    timeGrain: 'Monthly'
    timePeriod: { startDate: budgetStartDate }
    notifications: {
      actual80: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 80
        thresholdType: 'Actual'
        contactEmails: [ alertEmail ]
        contactGroups: [ actionGroup.id ]
      }
      actual100: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 100
        thresholdType: 'Actual'
        contactEmails: [ alertEmail ]
        contactGroups: [ actionGroup.id ]
      }
      forecast100: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 100
        thresholdType: 'Forecasted'
        contactEmails: [ alertEmail ]
        contactGroups: [ actionGroup.id ]
      }
    }
  }
}

output logicAppName string = logicApp.name
output actionGroupId string = actionGroup.id
