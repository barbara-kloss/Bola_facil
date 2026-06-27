import requests

api_key = '5592e468ca69d3400bfb13f95ad7f169'
headers = {'x-apisports-key': api_key}
res = requests.get('https://v3.football.api-sports.io/fixtures/lineups', params={'fixture': 537331}, headers=headers)
data = res.json()

print('Errors:', data.get('errors'))
resp = data.get('response', [])
if resp:
    home = resp[0]
    away = resp[1]
    print(f"Home Team: {home.get('team', {}).get('name')}")
    print("Home Starting XI (first 3):", [p['player']['name'] for p in home.get('startXI', [])[:3]])
    print(f"Away Team: {away.get('team', {}).get('name')}")
    print("Away Starting XI (first 3):", [p['player']['name'] for p in away.get('startXI', [])[:3]])
else:
    print('No response data.')
