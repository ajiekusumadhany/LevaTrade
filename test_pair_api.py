import requests
import json

response = requests.get('http://localhost:5000/api/pair-performance?mode=dry-run&days=30')
data = response.json()

print('Success:', data.get('success'))
print('Has pairs:', 'pairs' in data)

if 'pairs' in data:
    print('Pairs count:', len(data['pairs']))
    print('Sample pairs:', list(data['pairs'].keys())[:3] if data['pairs'] else 'None')
    
    # Show structure of first pair
    if data['pairs']:
        first_pair = list(data['pairs'].values())[0]
        print('First pair structure keys:', list(first_pair.keys()))
else:
    print('Error:', data.get('error', 'Unknown error'))