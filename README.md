# BolãoFácil

Jogue Junto. Torça. Ganhe.

Aplicação Flask para gerenciar bolões de futebol com cadastro de usuários, jogos, palpites, ranking, chat simples e notificações via WhatsApp.
Também integra a API football-data.org para sincronizar jogos do Brasileirão Série A (`BSA`) e salvar os dados localmente.

## Estrutura

- `app.py`: factory `create_app()`, blueprints, Flask-Login e inicialização do SQLite.
- `controllers/`: rotas de autenticação, jogos, palpites, ranking e WhatsApp.
- `models/`: data-access layer com `sqlite3` puro.
- `services/`: pontuação, notificações e integração WhatsApp.
- `services/football_service.py`: cliente football-data.org, sincronização local e limite de 10 req/min.
- `database/`: schema SQLite e seed.
- `templates/`, `static/`: interface em pt-BR.
- `tests/`: testes com pytest e banco SQLite temporário.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python database/seed.py
python app.py
```

Acesse `http://127.0.0.1:5000/login`.

Usuários do seed usam a senha `senha123`.

## Sincronizar jogos reais

Configure no `.env`:

```env
FOOTBALL_API_KEY=seu-token
FOOTBALL_API_URL=https://api.football-data.org/v4
```

Com o app rodando e logado, acesse:

```text
http://127.0.0.1:5000/admin/sync-games
```

A aplicação salva os jogos no SQLite e as telas usam o banco local, evitando chamadas à API em cada request.

## Testes

```bash
pytest tests/
```

## Regras de pontuação

| Acerto | Pontos |
| --- | ---: |
| Placar exato | 10 |
| Vencedor e gols de um time | 5 |
| Somente vencedor | 3 |
| Empate sem placar exato | 2 |
| Erro total | 0 |
