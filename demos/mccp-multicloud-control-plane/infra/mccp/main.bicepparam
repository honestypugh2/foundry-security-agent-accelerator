// Parameters come from environment variables so no email, tenant or account name is committed.
// infra/mccp/deploy.sh sets them for you; to deploy by hand:
//   export MCCP_ALERT_EMAIL=you@yourcompany.com
//   az deployment group create -g <rg> -f infra/mccp/main.bicep -p infra/mccp/main.bicepparam
using './main.bicep'

param alertEmail = readEnvironmentVariable('MCCP_ALERT_EMAIL')
param namePrefix = readEnvironmentVariable('MCCP_NAME_PREFIX', 'contosomccp')
param apimSku = readEnvironmentVariable('MCCP_APIM_SKU', 'BasicV2')

// Agent identity at the gateway: entra (default) or okta
param identityProvider = readEnvironmentVariable('MCCP_IDENTITY_PROVIDER', 'entra')
param oktaIssuer = readEnvironmentVariable('OKTA_ISSUER', 'https://contoso-health.okta.example/oauth2/default')
param oktaAudience = readEnvironmentVariable('OKTA_AUDIENCE', 'api://contoso-ai-gateway')
param entraAudience = readEnvironmentVariable('MCCP_ENTRA_AUDIENCE', 'https://cognitiveservices.azure.com')

// ATTACH to the Foundry account from infra/live.bicep (leave MCCP_EXISTING_FOUNDRY_ACCOUNT empty for NEW)
param existingFoundryAccountName = readEnvironmentVariable('MCCP_EXISTING_FOUNDRY_ACCOUNT', '')
param existingFoundryResourceGroup = readEnvironmentVariable('MCCP_EXISTING_FOUNDRY_RG', '')
param projectName = readEnvironmentVariable('MCCP_PROJECT_NAME', 'contoso-agents')
param modelDeploymentName = readEnvironmentVariable('MCCP_MODEL_DEPLOYMENT', 'policy-model')

// NEW mode model
param modelName = readEnvironmentVariable('MCCP_MODEL_NAME', 'gpt-5-mini')
param modelVersion = readEnvironmentVariable('MCCP_MODEL_VERSION', '2025-08-07')
param modelCapacity = int(readEnvironmentVariable('MCCP_MODEL_CAPACITY', '20'))

// FinOps limits
param tpmPerAgent = int(readEnvironmentVariable('MCCP_TPM_PER_AGENT', '20000'))
param monthlyTokenQuotaPerUser = int(readEnvironmentVariable('MCCP_USER_MONTHLY_TOKENS', '10500000'))
param monthlyTokenQuotaPerUserTier2 = int(readEnvironmentVariable('MCCP_USER_TIER2_MONTHLY_TOKENS', '21000000'))
param monthlyTokenQuotaPerAgent = int(readEnvironmentVariable('MCCP_AGENT_MONTHLY_TOKENS', '100000000'))
param budgetAmount = int(readEnvironmentVariable('MCCP_BUDGET_USD', '500'))
param perAgentHourlyTokenKillThreshold = int(readEnvironmentVariable('MCCP_KILL_TOKENS_PER_HOUR', '2000000'))
