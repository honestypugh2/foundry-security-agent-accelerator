// One role assignment: the API Management managed identity may call models on the Foundry account.
// Deployed at the Foundry account's resource group (works for NEW and ATTACH).
param accountName string
param principalId string

var cognitiveServicesOpenAiUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd' // Cognitive Services OpenAI User

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: accountName
}

resource apimOpenAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(account.id, principalId, cognitiveServicesOpenAiUserRoleId)
  scope: account
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAiUserRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

output roleAssignmentId string = apimOpenAiUser.id
