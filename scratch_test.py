import requests
import json

api_key = '6de3a3775b9ee3aca616e24dbcd42893'
headers = {'x-apisports-key': api_key}

res = requests.get('https://v3.football.api-sports.io/players', params={'id': 369, 'season': 2022}, headers=headers)
data = res.json()
print("Player details response status:", res.status_code)
print("Errors:", data.get('errors'))
print("Response length:", len(data.get('response', [])))
if data.get('response'):
    player_obj = data['response'][0]['player']
    print("Player name:", player_obj.get('name'))
    print("Player photo field value:", player_obj.get('photo'))
