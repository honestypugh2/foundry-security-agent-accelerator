// ATTACH mode: read-only lookup of the Foundry account created by infra/live.bicep (or any AIServices account).
// Deployed at the account's resource group scope. Creates nothing; fails fast if the account, project or
// model deployment does not exist.
param accountName string
param projectName string
param deploymentName string

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: accountName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' existing = {
  parent: account
  name: projectName
}

resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' existing = {
  parent: account
  name: deploymentName
}

output accountName string = account.name
output accountId string = account.id
output openAiEndpoint string = 'https://${account.properties.customSubDomainName}.openai.azure.com/'
output projectEndpoint string = project.properties.endpoints['AI Foundry API']
output deploymentName string = deployment.name
output modelName string = deployment.properties.model.name
