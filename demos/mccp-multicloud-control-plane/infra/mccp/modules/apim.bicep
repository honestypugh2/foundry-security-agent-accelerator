// Azure API Management as the AI gateway in front of Foundry.
param location string
param apimName string
param sku string = 'BasicV2'
param publisherEmail string
param publisherName string
@allowed([ 'entra', 'okta' ])
param identityProvider string = 'entra'
param oktaIssuer string
param oktaAudience string
param entraTenantId string
param entraAudience string = 'https://cognitiveservices.azure.com'
param foundryOpenAiEndpoint string
param appInsightsName string
param logAnalyticsId string
param tpmPerAgent int
param monthlyTokenQuotaPerAgent int
param monthlyTokenQuotaPerUser int
param monthlyTokenQuotaPerUserTier2 int

@description('Agents that get their own subscription (example two). Names match apim_subscription_id in data/mccp/agents.json.')
param agentSubscriptions array = [
  'contoso-claims-triage'
  'contoso-rev-cycle-coder'
]

resource apim 'Microsoft.ApiManagement/service@2024-05-01' = {
  name: apimName
  location: location
  sku: {
    name: sku
    capacity: 1
  }
  identity: { type: 'SystemAssigned' }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
  }
}

// ── Named values read by policies/ai-gateway.xml (updated at runtime by the kill switch) ──────────
// "none" is the empty-list sentinel: a named value "may not be empty or consist only of whitespace" (ARM reference).
var namedValues = [
  { name: 'killswitch-global', value: 'false' }
  { name: 'killed-agents', value: 'none' }
  { name: 'killed-users', value: 'none' }
  { name: 'quota-tier2-users', value: 'none' }
  { name: 'okta-issuer', value: oktaIssuer }
  { name: 'okta-audience', value: oktaAudience }
  { name: 'entra-tenant-id', value: entraTenantId }
  { name: 'entra-audience', value: entraAudience }
]

resource nv 'Microsoft.ApiManagement/service/namedValues@2024-05-01' = [for item in namedValues: {
  parent: apim
  name: item.name
  properties: {
    displayName: item.name
    value: item.value
    secret: false
  }
}]

// ── Backend: Foundry (Azure OpenAI-compatible endpoint); auth via authentication-managed-identity in the policy ─
resource backend 'Microsoft.ApiManagement/service/backends@2024-05-01' = {
  parent: apim
  name: 'foundry-openai'
  properties: {
    description: 'Microsoft Foundry model endpoint (Contoso Health agents)'
    protocol: 'http'
    url: '${foundryOpenAiEndpoint}openai'
  }
}

// ── API + operations ──────────────────────────────────────────────────────────────────────────
resource api 'Microsoft.ApiManagement/service/apis@2024-05-01' = {
  parent: apim
  name: 'ai'
  properties: {
    displayName: 'AI gateway (mccp)'
    path: 'ai/openai'
    protocols: [ 'https' ]
    subscriptionRequired: true
    serviceUrl: '${foundryOpenAiEndpoint}openai'
  }
}

resource opChat 'Microsoft.ApiManagement/service/apis/operations@2024-05-01' = {
  parent: api
  name: 'chat-completions'
  properties: {
    displayName: 'Chat completions'
    method: 'POST'
    urlTemplate: '/deployments/{deployment-id}/chat/completions'
    templateParameters: [
      { name: 'deployment-id', type: 'string', required: true }
    ]
  }
}

resource opResponses 'Microsoft.ApiManagement/service/apis/operations@2024-05-01' = {
  parent: api
  name: 'responses'
  properties: {
    displayName: 'Responses'
    method: 'POST'
    urlTemplate: '/responses'
  }
}

// Build-time edits to policies/ai-gateway.xml:
//  1. numeric limits replace the __TOKENS__;
//  2. the identity block that is NOT selected is turned into an XML comment (its markers become <!-- and -->).
var policyRaw = loadTextContent('../policies/ai-gateway.xml')
var policyStep1 = replace(policyRaw, '__TPM_PER_AGENT__', string(tpmPerAgent))
var policyStep2 = replace(policyStep1, '__AGENT_MONTHLY_TOKEN_QUOTA__', string(monthlyTokenQuotaPerAgent))
var policyStep3 = replace(policyStep2, '__USER_TIER2_MONTHLY_TOKEN_QUOTA__', string(monthlyTokenQuotaPerUserTier2))
var policyStep4 = replace(policyStep3, '__USER_MONTHLY_TOKEN_QUOTA__', string(monthlyTokenQuotaPerUser))
var disabled = identityProvider == 'okta' ? 'ENTRA' : 'OKTA'
var policyStep5 = replace(policyStep4, '<!--__${disabled}_BEGIN__-->', '<!-- ${toLower(disabled)} identity block disabled at deploy time')
var policyXml = replace(policyStep5, '<!--__${disabled}_END__-->', '-->')

resource apiPolicy 'Microsoft.ApiManagement/service/apis/policies@2024-05-01' = {
  parent: api
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: policyXml
  }
  dependsOn: [ nv, backend ]
}

// ── Observability ─────────────────────────────────────────────────────────────────────────────
resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource logger 'Microsoft.ApiManagement/service/loggers@2024-05-01' = {
  parent: apim
  name: 'appinsights'
  properties: {
    loggerType: 'applicationInsights'
    resourceId: appInsights.id
    credentials: {
      instrumentationKey: appInsights.properties.InstrumentationKey // documented credential for applicationInsights loggers
    }
  }
}

resource apiDiagnostics 'Microsoft.ApiManagement/service/apis/diagnostics@2024-05-01' = {
  parent: api
  name: 'applicationinsights'
  properties: {
    loggerId: logger.id
    alwaysLog: 'allErrors'
    metrics: true // required for llm-emit-token-metric custom metrics
    httpCorrelationProtocol: 'W3C'
    verbosity: 'information'
    sampling: {
      samplingType: 'fixed'
      percentage: 100
    }
    // LLM prompt/completion logging: enable in the portal (API → Settings → Azure Monitor → "Log LLM messages")
    // or via the diagnostics "largeLanguageModel" settings where your API version supports it. VALIDATE before enabling:
    // prompts may contain PHI — keep disabled for Contoso Health unless approved.
  }
}

resource apimDiag 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: apim
  properties: {
    workspaceId: logAnalyticsId
    logAnalyticsDestinationType: 'Dedicated'
    logs: [ { categoryGroup: 'allLogs', enabled: true } ]
    metrics: [ { category: 'AllMetrics', enabled: true } ]
  }
}

// The role assignment that lets this managed identity call Foundry models lives in foundry-access.bicep
// (deployed in the Foundry account's resource group, so it works for NEW and ATTACH mode).

// ── Product 'agents' with one subscription per agent (kill switch can suspend one) ─────────────
resource product 'Microsoft.ApiManagement/service/products@2024-05-01' = {
  parent: apim
  name: 'agents'
  properties: {
    displayName: 'Agents'
    description: 'One subscription per registered agent.'
    subscriptionRequired: true
    approvalRequired: false
    state: 'published'
  }
}

resource productApi 'Microsoft.ApiManagement/service/products/apis@2024-05-01' = {
  parent: product
  name: api.name
}

resource agentSubs 'Microsoft.ApiManagement/service/subscriptions@2024-05-01' = [for agentId in agentSubscriptions: {
  parent: apim
  name: 'agent-${agentId}'
  properties: {
    displayName: agentId
    scope: '/products/${product.name}' // documented format: /products/{productId}
    state: 'active'
  }
}]

output apimName string = apim.name
output apimId string = apim.id
output gatewayUrl string = apim.properties.gatewayUrl
output principalId string = apim.identity.principalId
