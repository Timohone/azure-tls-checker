# Azure TLS Checker using Azure Resource Graph

# Initialize results array
$results = @()

# Query all subscriptions for resources supporting TLS
$query = @"
resources
| where type in (
    'Microsoft.Web/sites',
    'Microsoft.Network/frontDoors',
    'Microsoft.Network/applicationGateways',
    'Microsoft.Sql/servers',
    'Microsoft.Storage/storageAccounts',
    'Microsoft.ApiManagement/service',
    'Microsoft.Search/searchServices',
    'Microsoft.CognitiveServices/accounts',
    'Microsoft.EventHub/namespaces',
    'Microsoft.ServiceBus/namespaces',
    'Microsoft.KeyVault/vaults',
    'Microsoft.Synapse/workspaces'
)
| extend tlsVersion = case(
    type == 'Microsoft.Web/sites', properties.siteConfig.minTlsVersion,
    type == 'Microsoft.Network/frontDoors', properties.frontendEndpoints[0].properties.minimumTlsVersion,
    type == 'Microsoft.Network/applicationGateways', properties.sslPolicy.minProtocolVersion,
    type == 'Microsoft.Sql/servers', properties.minimalTlsVersion,
    type == 'Microsoft.Storage/storageAccounts', properties.minimumTlsVersion,
    type == 'Microsoft.ApiManagement/service', properties.protocolSettings.tls.minProtocolVersion,
    type == 'Microsoft.Search/searchServices', properties.minimalTlsVersion,
    type == 'Microsoft.CognitiveServices/accounts', properties.networkAcls.defaultAction,
    type == 'Microsoft.EventHub/namespaces', properties.minimumTlsVersion,
    type == 'Microsoft.ServiceBus/namespaces', properties.minimumTlsVersion,
    type == 'Microsoft.KeyVault/vaults', properties.networkAcls.defaultAction,
    type == 'Microsoft.Synapse/workspaces', properties.tlsVersion,
    'Not Checked'
)
| project name, type, resourceGroup, subscriptionId, tlsVersion
"@

# Execute the query
$resources = az graph query -q $query --query "data" -o json | ConvertFrom-Json

foreach ($resource in $resources) {
    $results += [PSCustomObject]@{
        ResourceType = $resource.type
        ResourceName = $resource.name
        ResourceGroup = $resource.resourceGroup
        SubscriptionId = $resource.subscriptionId
        TLSVersion = if ($resource.tlsVersion -eq "") { "Not Configured" } else { $resource.tlsVersion }
    }
}

# Export results to a CSV file
$results | Export-Csv -Path "TLS_Versions_Report.csv" -NoTypeInformation

Write-Host "TLS version check complete using Azure Resource Graph. Results saved to TLS_Versions_Report.csv"
