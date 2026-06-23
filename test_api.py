import requests

api_key = '6de3a3775b9ee3aca616e24dbcd42893'
headers = {'x-apisports-key': api_key}

res = requests.get('https://v3.football.api-sports.io/leagues', params={'search': 'World Cup'}, headers=headers)
leagues = res.json().get('response', [])
for l in leagues:
    print("League:", l['league']['id'], "-", l['league']['name'], "- Seasons:", [s['year'] for s in l['seasons']])

res = requests.get('https://v3.football.api-sports.io/fixtures', params={'league': 1, 'season': 2022}, headers=headers)
fixtures = res.json().get('response', [])
if fixtures:
    print('Found fixtures:', len(fixtures))
    f = fixtures[0]
    print('Fixture Data keys:', f.keys())
    print('Fixture:', f['fixture'])
    print('League:', f['league'])
    print('Teams:', f['teams'])
    print('Goals:', f['goals'])
