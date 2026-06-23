from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.chat import ChatGroup, ChatGroupMember, ChatMessage
from models.user import User
from models.game import Game
from models.score import Score
from models.notification import Notification
from utils.messages import ApiMessages
import re

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat/bot", methods=["GET"])
@login_required
def bot_chat():
    messages = ChatMessage.list_private(current_user.id, 0)
    return render_template("chat/private.html", messages=messages)

@chat_bp.route("/chat/bot/send", methods=["POST"])
@login_required
def send_bot_message():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Mensagem vazia"}), 400
    
    ChatMessage.send_private(current_user.id, 0, text, is_bot=0)
    
    # Processa intenções do bot
    bot_reply = _generate_bot_reply(text, current_user)
    
    ChatMessage.send_private(0, current_user.id, bot_reply, is_bot=1)
    
    return jsonify({"success": True, "reply": bot_reply})


def _parse_bet_from_text(text: str):
    """
    Tenta extrair um palpite de jogo a partir de texto livre.
    Aceita formatos como:
      - "flamengo 2 x 1 vasco"
      - "flamengo 2x1 vasco"
      - "flamengo 2 a 1 vasco"
      - "#3 2x0"  (referência por número de jogo listado)
    Retorna dict com {home_team, away_team, home_score, away_score} ou None.
    """
    # Formato: "time_A [PLACAR] [x|a|-] [PLACAR] time_B"
    # ou "time_A [PLACARxPLACAR] time_B"
    patterns = [
        # "Flamengo 2 x 1 Vasco" ou "Flamengo 2-1 Vasco"
        r"^(.+?)\s+(\d+)\s*[x×a\-]\s*(\d+)\s+(.+)$",
        # "Flamengo 2x1 Vasco" (sem espaços em torno do x)
        r"^(.+?)\s+(\d+)[x×](\d+)\s+(.+)$",
    ]
    for pat in patterns:
        m = re.match(pat, text.strip(), re.IGNORECASE)
        if m:
            home_team = m.group(1).strip()
            home_score = int(m.group(2))
            away_score = int(m.group(3))
            away_team = m.group(4).strip()
            return {
                "home_team": home_team,
                "away_team": away_team,
                "home_score": home_score,
                "away_score": away_score,
            }
    return None


def _find_matching_game(home_team: str, away_team: str, pool_id=None):
    """
    Busca um jogo agendado que contenha os nomes dos times (busca parcial, case-insensitive).
    Retorna o objeto game ou None.
    """
    games = Game.list(pool_id)
    ht = home_team.lower().strip()
    at = away_team.lower().strip()
    scheduled = [g for g in games if g["status"] == "scheduled"]
    
    # Busca exata (parcial)
    for g in scheduled:
        gh = (g["home_team"] or "").lower()
        ga = (g["away_team"] or "").lower()
        if ht in gh and at in ga:
            return g
    
    # Busca invertida (usuário digitou visitante como mandante)
    for g in scheduled:
        gh = (g["home_team"] or "").lower()
        ga = (g["away_team"] or "").lower()
        if at in gh and ht in ga:
            return g
    
    return None


def _try_save_bet(user, parsed: dict, pool_id=None):
    """
    Tenta salvar uma aposta a partir de um palpite parseado.
    Retorna (success: bool, message: str).
    """
    from datetime import datetime, timedelta
    from flask import current_app
    
    game = _find_matching_game(parsed["home_team"], parsed["away_team"], pool_id)
    if not game:
        return False, (
            f"Não encontrei um jogo agendado com *{parsed['home_team']}* vs *{parsed['away_team']}*. "
            "Use *jogos* para ver os jogos disponíveis e copie os nomes dos times."
        )
    
    # Verificar lockout (30 min antes do jogo)
    try:
        from flask import current_app
        lockout_minutes = current_app.config.get("BET_LOCKOUT_MINUTES", 30)
    except Exception:
        lockout_minutes = 30
    
    try:
        match_dt = game["match_datetime"]
        if isinstance(match_dt, str):
            match_time = datetime.fromisoformat(match_dt.replace('Z', '+00:00'))
        else:
            match_time = match_dt
        now = datetime.now(match_time.tzinfo) if match_time.tzinfo else datetime.now()
        is_locked = (match_time - now) < timedelta(minutes=lockout_minutes)
    except Exception:
        is_locked = False
    
    if is_locked:
        return False, (
            f"⛔ O prazo para palpitar em *{game['home_team']} vs {game['away_team']}* já encerrou! "
            f"Os palpites fecham {lockout_minutes} minutos antes da partida."
        )
    
    # Garantir que o usuário está no pool
    from models.user import PoolMember
    if not PoolMember.exists(game["pool_id"], user.id):
        PoolMember.add(game["pool_id"], user.id)
    
    from models.bet import Bet
    Bet.create(user.id, game["id"], parsed["home_score"], parsed["away_score"])
    
    # Determina se foi atualização ou novo palpite
    return True, (
        f"✅ Palpite salvo! *{game['home_team']} {parsed['home_score']} x {parsed['away_score']} {game['away_team']}*. "
        "Boa sorte! 🍀"
    )


def _generate_bot_reply(text: str, user) -> str:
    """Gera uma resposta inteligente baseada em palavras-chave."""
    import random
    t = text.lower().strip()

    # ── Saudações ──────────────────────────────────────────────────────────────
    # Palavras de saudação como palavras completas ou início de frase
    saudacao_words = ["oi", "olá", "ola", "hey", "hi", "hello", "eai", "eaí", "opa"]
    saudacao_phrases = ["bom dia", "boa tarde", "boa noite", "boa semana", "tudo bem", "tudo bom"]
    
    is_saudacao = any(re.search(r'\b' + w + r'\b', t) for w in saudacao_words)
    if not is_saudacao:
        is_saudacao = any(p in t for p in saudacao_phrases)
    
    if is_saudacao:
        saudacoes = [
            f"Olá, {user.name}! 👋 Como posso te ajudar hoje? Digite *ajuda* para ver os comandos.",
            f"Oi {user.name}! Que bom te ver por aqui! 😄 Precisa de algo?",
            f"Eai {user.name}! Preparado para acertar os palpites? ⚽",
            f"Olá! Sou o assistente do BolãoFácil. Para fazer um palpite pelo chat, envie no formato: *Time A 2 x 1 Time B*",
        ]
        return random.choice(saudacoes)

    # ── Palpite direto via texto ───────────────────────────────────────────────
    # Verificar se é uma tentativa de palpite (tem número + x/a/-)
    has_score_pattern = bool(re.search(r'\d+\s*[x×a\-]\s*\d+', t))
    is_bet_intent = any(w in t for w in ["palpito", "aposto", "chuto"]) or has_score_pattern
    
    if has_score_pattern:
        parsed = _parse_bet_from_text(text)
        if parsed:
            try:
                from models.user import Pool
                pool = Pool.get_default()
                pool_id = pool["id"] if pool else None
                success, msg = _try_save_bet(user, parsed, pool_id)
                return msg
            except Exception as e:
                return f"Não consegui salvar o palpite. Erro: {str(e)[:80]}. Tente pela página de Jogos."

    # ── Listar jogos disponíveis para palpite ─────────────────────────────────
    if any(w in t for w in ["listar jogos", "lista de jogos", "jogos disponíveis", "jogos disponiveis", "quais jogos"]):
        try:
            from models.user import Pool
            pool = Pool.get_default()
            games = Game.list(pool["id"] if pool else None)
            agendados = [g for g in games if g["status"] == "scheduled"][:8]
            if agendados:
                linhas = ["**Jogos disponíveis para palpite:**"]
                for i, g in enumerate(agendados, 1):
                    dt = str(g["match_datetime"])[:16].replace("T", " ")
                    linhas.append(f"*{i}.* {g['home_team']} vs {g['away_team']} — {dt}")
                linhas.append("\nPara palpitar, envie: *Nome do time A [placar] x [placar] Nome do time B*")
                linhas.append("Exemplo: *Flamengo 2 x 1 Vasco*")
                return "\n".join(linhas)
        except Exception:
            pass
        return "Não há jogos disponíveis para palpite no momento."

    # ── Ranking ───────────────────────────────────────────────────────────────
    if any(w in t for w in ["ranking", "classificação", "classificacao", "lider", "líder", "primeiro"]):
        try:
            from models.user import Pool
            pool = Pool.get_default()
            if pool:
                ranking = Score.get_ranking(pool["id"])
                if ranking:
                    top = ranking[:3]
                    linhas = ["**🏆 Top Ranking:**"]
                    medals = ["🥇", "🥈", "🥉"]
                    for i, r in enumerate(top):
                        linhas.append(f"{medals[i]} {r['name']} — {r['total_points']} pts")
                    return "\n".join(linhas)
        except Exception:
            pass
        return "Não consegui acessar o ranking agora. 😕 Tente visitar a página de Ranking."

    # ── Próximos jogos ────────────────────────────────────────────────────────
    if any(w in t for w in ["jogo", "partida", "próximo", "proximo", "hoje", "quando", "agenda"]):
        try:
            from models.user import Pool
            pool = Pool.get_default()
            games = Game.list(pool["id"] if pool else None)
            agendados = [g for g in games if g["status"] == "scheduled"][:5]
            if agendados:
                linhas = ["**⚽ Próximos jogos:**"]
                for g in agendados:
                    dt = str(g["match_datetime"])[:16].replace("T", " ")
                    linhas.append(f"• {g['home_team']} vs {g['away_team']} — {dt}")
                linhas.append("\nDigite *listar jogos* para ver todos e fazer seu palpite!")
                return "\n".join(linhas)
        except Exception:
            pass
        return "Não há jogos agendados no momento."

    # ── Palpite / Apostar (intenção sem placar) ───────────────────────────────
    if any(w in t for w in ["palpite", "apostar", "aposta", "chutar", "placar"]):
        return (
            "Para fazer um palpite pelo chat, envie no formato:\n"
            "*Time A [placar] x [placar] Time B*\n\n"
            "Exemplo: *Flamengo 2 x 1 Vasco*\n\n"
            "Ou acesse a página de **Jogos** e clique em *Palpitar*!\n"
            "Digite *listar jogos* para ver os jogos disponíveis."
        )

    # ── Pontuação própria ─────────────────────────────────────────────────────
    if any(w in t for w in ["ponto", "pontos", "minha pontuação", "quantos pontos", "score", "pontuação"]):
        try:
            from models.user import Pool
            pool = Pool.get_default()
            if pool:
                ranking = Score.get_ranking(pool["id"])
                for r in ranking:
                    if str(r["user_id"]) == str(user.id):
                        pos = ranking.index(r) + 1
                        return f"Você está na **{pos}ª posição** com **{r['total_points']} pontos**! Continue assim! 🏆"
                return "Você ainda não tem pontos registrados. Faça seus palpites!"
        except Exception:
            pass
        return "Não consegui acessar sua pontuação agora."

    # ── Meus palpites ─────────────────────────────────────────────────────────
    if any(w in t for w in ["meu palpite", "meus palpites", "histórico", "historico", "acertei", "errei"]):
        return "Veja seu histórico completo de palpites em **Meus Palpites** no menu do usuário! 📊"

    # ── Ajuda / comandos ──────────────────────────────────────────────────────
    if any(w in t for w in ["ajuda", "help", "comando", "o que você faz", "o que vc faz", "como", "como funciona"]):
        return (
            "**🤖 Comandos disponíveis:**\n"
            "• *oi* / *olá* — saudação\n"
            "• *ranking* — ver o top ranking\n"
            "• *jogos* — próximos jogos\n"
            "• *listar jogos* — todos os jogos com índice\n"
            "• *pontos* — sua pontuação\n"
            "• *histórico* — seus palpites\n\n"
            "**⚽ Para fazer um palpite pelo chat:**\n"
            "Envie: *Time A [placar] x [placar] Time B*\n"
            "Exemplo: *Flamengo 2 x 1 Vasco*"
        )

    # ── Respostas padrão variadas ─────────────────────────────────────────────
    respostas_padrao = [
        "Hmm, não entendi muito bem. Digite *ajuda* para ver o que posso fazer!",
        "Não sei responder isso ainda. Tente *ajuda* para ver meus comandos.",
        "Boa pergunta! Mas ainda não sei responder isso. Tente *ranking*, *jogos* ou *pontos*.",
        "Ops! Não entendi. Que tal tentar *ajuda* para ver os comandos disponíveis?\n\nPara fazer palpite: *Flamengo 2 x 1 Vasco*",
    ]
    return random.choice(respostas_padrao)

@chat_bp.route("/chat/grupos", methods=["GET"])
@login_required
def list_groups():
    groups = ChatGroup.list_for_user(current_user.id)
    return render_template("chat/grupos.html", groups=groups)

@chat_bp.route("/chat/grupos/criar", methods=["POST"])
@login_required
def create_group():
    data = request.get_json() or request.form
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Nome do grupo é obrigatório"}), 400
    
    group = ChatGroup.create(name, current_user.id)
    return jsonify({"success": True, "group_id": group["id"]})

@chat_bp.route("/chat/grupos/<int:group_id>", methods=["GET"])
@login_required
def group_chat(group_id):
    if not ChatGroupMember.exists(group_id, current_user.id):
        return render_template("errors/403.html"), 403
    
    group = ChatGroup.get_by_id(group_id)
    messages = ChatMessage.list_for_group(group_id)
    return render_template("chat/group.html", group=group, messages=messages)

@chat_bp.route("/chat/grupos/<int:group_id>/send", methods=["POST"])
@login_required
def send_group_message(group_id):
    if not ChatGroupMember.exists(group_id, current_user.id):
        return jsonify({"error": "Não autorizado"}), 403
    
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Mensagem vazia"}), 400
    
    ChatMessage.send_to_group(group_id, current_user.id, text)
    return jsonify({"success": True})

@chat_bp.route("/chat/grupos/<int:group_id>/convidar", methods=["POST"])
@login_required
def invite_to_group(group_id):
    if not ChatGroupMember.exists(group_id, current_user.id):
        return jsonify({"error": "Não autorizado"}), 403
    
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    if not email:
        return jsonify({"error": "E-mail vazio"}), 400
    
    invited_user = User.get_by_email(email)
    
    if invited_user:
        if ChatGroupMember.exists(group_id, invited_user.id):
            return jsonify({"error": "Usuário já está no grupo"}), 400
        
        ChatGroupMember.add(group_id, invited_user.id)
        group = ChatGroup.get_by_id(group_id)
        
        Notification.create(
            user_id=invited_user.id,
            type="group_invite",
            title="Novo Convite de Grupo",
            body=f"{current_user.name} te adicionou ao grupo {group['name']}.",
            extra_data={"group_id": group_id}
        )
        return jsonify({"message": "Usuário adicionado com sucesso!"})
    else:
        from models.chat import ChatGroupInvite
        from services.email_service import EmailService
        
        ChatGroupInvite.add(group_id, email, current_user.id)
        group = ChatGroup.get_by_id(group_id)
        
        register_url = request.host_url.rstrip("/") + "/cadastro"
        EmailService.send_group_invite(
            to_email=email,
            inviter_name=current_user.name,
            group_name=group["name"],
            register_url=register_url
        )
        
        return jsonify({"message": f"Convite enviado para {email}! O usuário receberá um e-mail com instruções e será adicionado ao grupo ao criar sua conta."})
