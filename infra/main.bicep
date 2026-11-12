targetScope = 'resourceGroup'

param location string = resourceGroup().location
param searchLocation string = location
@minLength(3)
param name string
param projectName string = 'security-project'
param enableMonitoring bool = false
param enableLiveServices bool = false
param principalId string = ''
param modelDeploymentName string = 'policy-model'
param modelName string = 'gpt-5-mini'
param modelVersion string = '2025-08-07'
@minValue(1)
param modelCapacity int = 10
@allowed([
  'GlobalStandard'
  'DataZoneStandard'
  'Standard'
])
param modelSku string = 'GlobalStandard'
param tags object = {
  purpose: 'synthetic-security-lab'
}

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: name
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: name
    disableLocalAuth: true
    allowProjectManagement: true
    publicNetworkAccess: 'Enabled'
  }
  tags: tags
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: account
  name: projectName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
  tags: tags
  dependsOn: [
    deployment
  ]
}

output accountId string = account.id
output projectId string = project.id

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = if (enableMonitoring) {
  name: '${name}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    workspaceCapping: {
      dailyQuotaGb: json('0.1')
    }
  }
  tags: tags
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = if (enableMonitoring) {
  name: '${name}-insights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace!.id
  }
  tags: tags
}

output appInsightsResourceId string = enableMonitoring ? appInsights!.id : ''
output logAnalyticsResourceId string = enableMonitoring ? workspace!.id : ''

resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = if (enableLiveServices) {
  parent: account
  name: modelDeploymentName
  sku: {
    name: modelSku
    capacity: modelCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
    versionUpgradeOption: 'NoAutoUpgrade'
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}

resource search 'Microsoft.Search/searchServices@2025-05-01' = if (enableLiveServices) {
  name: '${name}-search'
  location: searchLocation
  sku: {
    name: 'basic'
  }
  properties: {
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
    replicaCount: 1
    partitionCount: 1
    semanticSearch: 'disabled'
  }
  tags: tags
}

resource safety 'Microsoft.CognitiveServices/accounts@2025-06-01' = if (enableLiveServices) {
  name: '${name}-safety'
  location: location
  kind: 'ContentSafety'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: '${name}-safety'
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
  }
  tags: tags
}

var assignRoles = enableLiveServices && !empty(principalId)
var foundryRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '53ca6127-db72-4b80-b1b0-d745d6d5456d')
var searchServiceRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
var searchDataRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
var safetyRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')
var logsRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '73c42c96-874c-492b-b04d-ab87d138a893')

resource foundryAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignRoles) {
  name: guid(account.id, principalId, foundryRole)
  scope: account
  properties: {
    roleDefinitionId: foundryRole
    principalId: principalId
    principalType: 'User'
  }
}

resource searchServiceAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignRoles) {
  name: guid(search!.id, principalId, searchServiceRole)
  scope: search
  properties: {
    roleDefinitionId: searchServiceRole
    principalId: principalId
    principalType: 'User'
  }
}

resource searchDataAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignRoles) {
  name: guid(search!.id, principalId, searchDataRole)
  scope: search
  properties: {
    roleDefinitionId: searchDataRole
    principalId: principalId
    principalType: 'User'
  }
}

resource safetyAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignRoles) {
  name: guid(safety!.id, principalId, safetyRole)
  scope: safety
  properties: {
    roleDefinitionId: safetyRole
    principalId: principalId
    principalType: 'User'
  }
}

resource logsAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignRoles && enableMonitoring) {
  name: guid(workspace!.id, principalId, logsRole)
  scope: workspace
  properties: {
    roleDefinitionId: logsRole
    principalId: principalId
    principalType: 'User'
  }
}

output accountName string = account.name
output projectEndpoint string = project.properties.endpoints['AI Foundry API']
output modelDeployment string = enableLiveServices ? deployment!.name : ''
output searchEndpoint string = enableLiveServices ? 'https://${search!.name}.search.windows.net' : ''
output safetyEndpoint string = enableLiveServices ? safety!.properties.endpoint : ''
output logsWorkspaceId string = enableMonitoring ? workspace!.properties.customerId : ''
output appInsightsName string = enableMonitoring ? appInsights!.name : ''
