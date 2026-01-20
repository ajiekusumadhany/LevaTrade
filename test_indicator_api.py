import requests
import json

response = requests.get('http://localhost:5000/api/indicator-performance?mode=dry-run&days=30')
data = response.json()

print('Success:', data.get('success'))
print('Has indicators:', 'indicators' in data)

if 'indicators' in data:
    print('Indicators count:', len(data['indicators']))
    print('Sample indicators:', list(data['indicators'].keys())[:3] if data['indicators'] else 'None')
    
    # Show structure of first indicator
    if data['indicators']:
        first_indicator = list(data['indicators'].values())[0]
        print('First indicator structure keys:', list(first_indicator.keys()))
        print('Has overall_accuracy:', 'overall_accuracy' in first_indicator)
        print('Has description:', 'description' in first_indicator)
else:
    print('Error:', data.get('error', 'Unknown error'))