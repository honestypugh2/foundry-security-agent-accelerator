// mccp — Multi-cloud AI Control Plane (Contoso Health demo)
// Deploys the API Management AI gateway (with the mccp policy), Log Analytics + App Insights for the gateway,
// and the automated kill switch (alert -> action group -> Logic App -> APIM named value) plus a budget.
//
// Two ways to get a model behind the gateway:
//   * NEW     (default)  create a Foundry (AIServices) account + project + model deployment in this resource group.
//   * ATTACH  set existingFoundryAccountName to reuse the Foundry account that infra/live.bicep already created
//             (fsa-<suffix>, project 'security-project', deployment 'policy-model'). Nothing in that account is
//             changed: the only write is one role assignment that lets the gateway's managed identity call models.
//
// Deploy with infra/mccp/deploy.sh (preflight + what-if + deploy + .env output) or:
//   az deployment group create -g <rg> -f infra/mccp/main.bicep -p infra/mccp/main.bicepparam
targetScope = 'resourceGroup'

@description('Azure region for the gateway, monitoring and kill switch.')
param location string = resourceGroup().location

@description('Short prefix for resource names (lowercase letters/numbers).')
@minLength(3)
@maxLength(12)
param namePrefix string = 'contosomccp'

@description('Email that receives budget and kill-switch alerts. Also used as the API Management publisher email.')
param alertEmail string

@description('API Management publisher email (defaults to alertEmail).')
param publisherEmail string = alertEmail

@description('API Management publisher name.')
param publisherName string = 'Contoso Health AI Platform'

@description('API Management SKU. BasicV2 is the lowest v2 tier; llm-token-limit and llm-emit-token-metric apply to classic and v2 tiers.')
@allowed([ 'Developer', 'BasicV2', 'StandardV2', 'PremiumV2', 'Basic', 'Standard', 'Premium' ])
param apimSku string = 'BasicV2'

// ── Agent identity at the gateway ────────────────────────────────────────────────────────────────
@description('Which identity provider the gateway trusts: entra (works with az login / managed identity, no extra setup) or okta (needs a real Okta authorization server).')
@allowed([ 'entra', 'okta' ])
param identityProvider string = 'entra'

@description('Okta custom authorization server issuer. Only used when identityProvider = okta.')
param oktaIssuer string = 'https://contoso-health.okta.example/oauth2/default'

@description('Audience expected in Okta access tokens. Only used when identityProvider = okta.')
param oktaAudience string = 'api://contoso-ai-gateway'

@description('Entra tenant whose tokens the gateway accepts.')
param entraTenantId string = tenant().tenantId

@description('Audience expected in Entra tokens. The default matches `az account get-access-token --resource https://cognitiveservices.azure.com`; use your own app registration (api://...) in production.')
param entraAudience string = 'https://cognitiveservices.azure.com'

// ── Model ────────────────────────────────────────────────────────────────────────────────────────
@description('ATTACH mode: name of an existing Foundry (AIServices) account to put behind the gateway. Empty = create a new one.')
param existingFoundryAccountName string = ''

@description('ATTACH mode: resource group of the existing Foundry account. Empty = this resource group.')
param existingFoundryResourceGroup string = ''

@description('Foundry project name (ATTACH: the existing project, e.g. security-project; NEW: the project to create).')
param projectName string = 'contoso-agents'

@description('Model deployment name the gateway routes to (ATTACH: must already exist, e.g. policy-model).')
param modelDeploymentName string = 'policy-model'

@description('NEW mode: model to deploy. gpt-5-mini 2025-08-07 is GA; check the Foundry model retirement schedule before changing.')
param modelName string = 'gpt-5-mini'

@description('NEW mode: model version.')
param modelVersion string = '2025-08-07'

@description('NEW mode: GlobalStandard capacity in thousands of tokens per minute (needs that much free quota in the region).')
@minValue(1)
param modelCapacity int = 20

// ── FinOps limits ────────────────────────────────────────────────────────────────────────────────
@description('Per-user monthly token quota (finops.py converts the $40 standard limit to tokens).')
param monthlyTokenQuotaPerUser int = 10500000

@description('Per-user monthly token quota after an approved increase ($80).')
param monthlyTokenQuotaPerUserTier2 int = 21000000

@description('Per-agent monthly token quota.')
param monthlyTokenQuotaPerAgent int = 100000000

@description('Per-agent tokens-per-minute burst limit.')
param tpmPerAgent int = 20000

@description('Monthly Azure budget (USD) for this resource group.')
param budgetAmount int = 500

@description('Token threshold per agent per hour that triggers the automatic kill (scheduled query alert).')
param perAgentHourlyTokenKillThreshold int = 2000000

@description('Budget start date (first day of the current month).')
param budgetStartDate string = '${utcNow('yyyy-MM')}-01'

var useExistingFoundry = !empty(existingFoundryAccountName)
var foundryRg = empty(existingFoundryResourceGroup) ? resourceGroup().name : existingFoundryResourceGroup
var suffix = uniqueString(resourceGroup().id)
var names = {
  logAnalytics: '${namePrefix}-law-${suffix}'
  appInsights: '${namePrefix}-appi-${suffix}'
  foundry: toLower('${namePrefix}ai${suffix}')
  apim: '${namePrefix}-apim-${suffix}'
  logicApp: '${namePrefix}-killswitch-${suffix}'
  actionGroup: '${namePrefix}-ag-killswitch'
}

// The gateway gets its own workspace: the base repo's lab workspace has a 0.1 GB/day cap, and an
// ingestion stop there would silently stop the automatic kill alert.
module monitoring 'modules/monitoring.bicep' = {
  name: 'mccp-monitoring'
  params: {
    location: location
    logAnalyticsName: names.logAnalytics
    appInsightsName: names.appInsights
  }
}

module foundryNew 'modules/foundry.bicep' = if (!useExistingFoundry) {
  name: 'mccp-foundry'
  params: {
    location: location
    accountName: names.foundry
    projectName: projectName
    deploymentName: modelDeploymentName
    modelName: modelName
    modelVersion: modelVersion
    modelCapacity: modelCapacity
    logAnalyticsId: monitoring.outputs.logAnalyticsId
  }
}

module foundryExisting 'modules/foundry-existing.bicep' = if (useExistingFoundry) {
  name: 'mccp-foundry-existing'
  scope: resourceGroup(foundryRg)
  params: {
    accountName: existingFoundryAccountName
    projectName: projectName
    deploymentName: modelDeploymentName
  }
}

var foundryAccountName = useExistingFoundry ? foundryExisting!.outputs.accountName : foundryNew!.outputs.accountName
var foundryOpenAiEndpoint = useExistingFoundry ? foundryExisting!.outputs.openAiEndpoint : foundryNew!.outputs.openAiEndpoint
var foundryProjectEndpoint = useExistingFoundry ? foundryExisting!.outputs.projectEndpoint : foundryNew!.outputs.projectEndpoint
var foundryDeploymentName = useExistingFoundry ? foundryExisting!.outputs.deploymentName : foundryNew!.outputs.deploymentName

module apim 'modules/apim.bicep' = {
  name: 'mccp-apim'
  params: {
    location: location
    apimName: names.apim
    sku: apimSku
    publisherEmail: publisherEmail
    publisherName: publisherName
    identityProvider: identityProvider
    oktaIssuer: oktaIssuer
    oktaAudience: oktaAudience
    entraTenantId: entraTenantId
    entraAudience: entraAudience
    foundryOpenAiEndpoint: foundryOpenAiEndpoint
    appInsightsName: monitoring.outputs.appInsightsName
    logAnalyticsId: monitoring.outputs.logAnalyticsId
    tpmPerAgent: tpmPerAgent
    monthlyTokenQuotaPerAgent: monthlyTokenQuotaPerAgent
    monthlyTokenQuotaPerUser: monthlyTokenQuotaPerUser
    monthlyTokenQuotaPerUserTier2: monthlyTokenQuotaPerUserTier2
  }
}

// The gateway's managed identity may call models on the Foundry account (new or existing).
module foundryAccess 'modules/foundry-access.bicep' = {
  name: 'mccp-foundry-access'
  scope: resourceGroup(foundryRg)
  params: {
    accountName: foundryAccountName
    principalId: apim.outputs.principalId
  }
}

module killswitch 'modules/killswitch.bicep' = {
  name: 'mccp-killswitch'
  params: {
    location: location
    apimName: apim.outputs.apimName
    logicAppName: names.logicApp
    actionGroupName: names.actionGroup
    alertEmail: alertEmail
    appInsightsId: monitoring.outputs.appInsightsId
    budgetAmount: budgetAmount
    budgetStartDate: budgetStartDate
    perAgentHourlyTokenKillThreshold: perAgentHourlyTokenKillThreshold
  }
}

output MCCP_FOUNDRY_MODE string = useExistingFoundry ? 'attach' : 'new'
output MCCP_IDENTITY_PROVIDER string = identityProvider
output APIM_GATEWAY_URL string = apim.outputs.gatewayUrl
output APIM_RESOURCE_ID string = apim.outputs.apimId
output FOUNDRY_ACCOUNT_NAME string = foundryAccountName
output FOUNDRY_PROJECT_ENDPOINT string = foundryProjectEndpoint
output FOUNDRY_MODEL_DEPLOYMENT string = foundryDeploymentName
output APPLICATIONINSIGHTS_NAME string = monitoring.outputs.appInsightsName
output LOG_ANALYTICS_WORKSPACE_ID string = monitoring.outputs.logAnalyticsCustomerId
output KILLSWITCH_LOGIC_APP_NAME string = killswitch.outputs.logicAppName
