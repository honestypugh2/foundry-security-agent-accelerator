targetScope = 'subscription'

param location string
param searchLocation string = location
@minLength(3)
param resourceGroupName string
@minLength(36)
@maxLength(36)
param principalId string
param projectName string = 'security-project'
param modelName string = 'gpt-5-mini'
param modelVersion string = '2025-08-07'
param modelDeploymentName string = 'policy-model'
@minValue(1)
param modelCapacity int = 10

resource lab 'Microsoft.Resources/resourceGroups@2025-04-01' = {
  name: resourceGroupName
  location: location
  tags: {
    purpose: 'synthetic-security-lab'
    reviewWindow: '24-hours'
  }
}

module services './main.bicep' = {
  name: 'synthetic-live-services'
  scope: lab
  params: {
    location: location
    searchLocation: searchLocation
    name: 'fsa-${uniqueString(lab.id)}'
    projectName: projectName
    enableMonitoring: true
    enableLiveServices: true
    principalId: principalId
    modelDeploymentName: modelDeploymentName
    modelName: modelName
    modelVersion: modelVersion
    modelCapacity: modelCapacity
  }
}

output resourceGroup string = lab.name
output configuration object = services.outputs
