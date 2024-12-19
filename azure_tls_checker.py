import subprocess
import json
import csv

# Optimized query to fetch TLS configurations for all supported resource types
QUERY = """
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
    'Not Configured'
)
| project name, type, resourceGroup, subscriptionId, tlsVersion
"""

def run_command(command):
    """Runs a shell command and returns the output as JSON."""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e.stderr.decode()}")
        return None

def get_subscriptions():
    """Fetches all subscriptions available to the current Azure account."""
    command = "az account list --query '[?state==`\"Enabled\"`].id' -o json"
    return run_command(command)

def main():
    print("Starting Azure TLS Checker for All Subscriptions...\n")

    # Get all subscriptions
    subscriptions = get_subscriptions()
    if not subscriptions:
        print("Failed to fetch subscriptions. Ensure Azure CLI is logged in.")
        return

    print(f"Found {len(subscriptions)} enabled subscriptions.\n")

    # Prepare output file
    output_file = "TLS_Versions_Report_All_Subscriptions.csv"
    results = []

    # Loop through each subscription
    for subscription in subscriptions:
        print(f"Switching to subscription: {subscription}")
        subprocess.run(f"az account set --subscription {subscription}", shell=True, check=True)

        print("Running Azure Resource Graph query...")
        query_command = f"az graph query -q \"{QUERY}\" --query \"data\" -o json"
        resources = run_command(query_command)

        if resources:
            print(f"Fetched {len(resources)} resources from subscription {subscription}.")
            results.extend(resources)
        else:
            print(f"No resources found in subscription {subscription} or query failed.")

    # Save results to a CSV file
    print(f"Saving results to {output_file}...")
    with open(output_file, "w", newline="") as csvfile:
        fieldnames = ["name", "type", "resourceGroup", "subscriptionId", "tlsVersion"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nTLS version check complete. Results saved to {output_file}.")

if __name__ == "__main__":
    main()
