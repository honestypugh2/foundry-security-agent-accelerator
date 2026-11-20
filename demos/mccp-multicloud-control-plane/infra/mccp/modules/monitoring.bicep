// Log Analytics workspace + workspace-based Application Insights for the gateway.
param location string
param logAnalyticsName string
param appInsightsName string
param retentionInDays int = 30

resource law 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: retentionInDays
  }
}

resource appi 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: law.id
    IngestionMode: 'LogAnalytics'
  }
}

output logAnalyticsId string = law.id
output logAnalyticsCustomerId string = law.properties.customerId
output appInsightsId string = appi.id
output appInsightsName string = appi.name
