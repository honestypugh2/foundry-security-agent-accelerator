// NEW mode: Microsoft Foundry AIServices account (project management enabled), one project, one model deployment.
param location string
param accountName string
param projectName string
param deploymentName string
param modelName string
param modelVersion string
param modelCapacity int
param logAnalyticsId string

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: accountName
  location: location
  kind: 'AIServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    allowProjectManagement: true
    customSubDomainName: accountName
    disableLocalAuth: true // keys off: APIM and agents use Entra ID
    publicNetworkAccess: 'Enabled' // use private endpoints for production
  }
}

resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: account
  name: deploymentName
  sku: {
    name: 'GlobalStandard'
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

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: account
  name: projectName
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    displayName: 'Contoso Health agents'
    description: 'Agents governed by the mccp control plane (demo, synthetic data).'
  }
  dependsOn: [ deployment ] // account-level child operations run one at a time
}

resource diag 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: account
  properties: {
    workspaceId: logAnalyticsId
    logs: [ { categoryGroup: 'allLogs', enabled: true } ]
    metrics: [ { category: 'AllMetrics', enabled: true } ]
  }
}

output accountName string = account.name
output accountId string = account.id
output openAiEndpoint string = 'https://${account.properties.customSubDomainName}.openai.azure.com/'
output projectEndpoint string = project.properties.endpoints['AI Foundry API']
output deploymentName string = deployment.name
