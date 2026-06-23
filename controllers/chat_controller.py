from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.chat import ChatGroup, ChatGroupMember, ChatMessage
from models.user import User
from models.notification import Notification
from utils.messages import ApiMessages

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
    
    bot_reply = _generate_bot_reply(text, current_user)
    ChatMessage.send_private(0, current_user.id, bot_reply, is_bot=1)
    
    return jsonify({"success": True})


def _generate_bot_reply(text: str, user) -> str:
    """Gera uma resposta inteligente baseada em palavras-chave."""
    import random
    t = text.lower().strip()

    # Saudações
    if any(w in t for w in ["oi", "olá", "ola", "boa", "bom dia", "boa tarde", "boa noite", "hey", "hi"]):
        saudacoes = [
            f"Olá, {user.name}! 👋 Como posso te ajudar hoje? Digite *ajuda* para ver os comandos.",
            f"Oi {user.name}! 😄 Que bom te ver por aqui! Precisa de algo?",
            f"Eai {user.name}! Preparado para acertar os palpites? ⚽",
        ]
        return random.choice(saudacoes)

    # Ranking
    if any(w in t for w in ["ranking", "classificação", "classificacao", "lider", "líder", "primeiro"]):
        try:
            from models.score import Score
            from models.user import Pool
            pool = Pool.get_default()
            if pool:
                ranking = Score.get_ranking(pool["id"])
                if ranking:
                    top = ranking[:3]
                    linhas = [f"🏆 **Top Ranking:**"]
                    medals = ["🥇", "🥈", "🥉"]
                    for i, r in enumerate(top):
                        linhas.append(f"{medals[i]} {r['name']} — {r['total_points']} pts")
                    return "\n".join(linhas)
        except Exception:
            pass
        return "Não consegui acessar o ranking agora. 😕 Tente visitar a página de Ranking."

    # Próximos jogos
    if any(w in t for w in ["jogo", "partida", "próximo", "proximo", "hoje", "quando"]):
        try:
            from models.game import Game
            from models.user import Pool
            pool = Pool.get_default()
            games = Game.list(pool["id"] if pool else None)
            agendados = [g for g in games if g["status"] == "scheduled"][:3]
            if agendados:
                linhas = ["⚽ **Próximos jogos:**"]
                for g in agendados:
                    dt = str(g["match_datetime"])[:16].replace("T", " ")
                    linhas.append(f"• {g['home_team']} vs {g['away_team']} — {dt}")
                return "\n".join(linhas)
        except Exception:
            pass
        return "Não há jogos agendados no momento. ⚽"

    # Palpites / Apostar
    if any(w in t for w in ["palpite", "apostar", "aposta", "chutar", "placar"]):
        return "Para fazer um palpite, acesse a página de **Jogos** e clique em *Palpitar* no jogo desejado! 🎯"

    # Pontuação própria
    if any(w in t for w in ["ponto", "pontos", "minha pontuação", "quantos pontos", "score"]):
        try:
            from models.score import Score
            from models.user import Pool
            pool = Pool.get_default()
            if pool:
                ranking = Score.get_ranking(pool["id"])
                for r in ranking:
                    if str(r["user_id"]) == str(user.id):
                        pos = ranking.index(r) + 1
                        return f"⭐ Você está na **{pos}ª posição** com **{r['total_points']} pontos**! Continue assim!"
                return "Você ainda não tem pontos registrados. Faça seus palpites! 🎯"
        except Exception:
            pass
        return "Não consegui acessar sua pontuação agora."

    # Meus palpites
    if any(w in t for w in ["meu palpite", "meus palpites", "histórico", "historico", "acertei", "errei"]):
        return "Veja seu histórico completo de palpites em **Meus Palpites** no menu do usuário! 📋"

    # Ajuda / comandos
    if any(w in t for w in ["ajuda", "help", "comando", "o que você faz", "o que vc faz"]):
        return (
            "🤖 **Comandos disponíveis:**\n"
            "• *ranking* — ver o top ranking\n"
            "• *jogos* — próximos jogos\n"
            "• *palpite* — como fazer um palpite\n"
            "• *pontos* — sua pontuação\n"
            "• *histórico* — seus palpites\n"
            "• *oi* — saudação 😄"
        )

    # Respostas padrão variadas
    respostas_padrao = [
        "Hmm, não entendi muito bem. 🤔 Digite *ajuda* para ver o que posso fazer!",
        "Não sei responder isso ainda, mas estou aprendendo! 😅 Tente *ajuda* para ver meus comandos.",
        "Boa pergunta! Mas ainda não sei responder isso. Tente *ranking*, *jogos* ou *pontos*. ⚽",
        "Ops! Não entendi. Que tal tentar *ajuda* para ver os comandos disponíveis? 🤖",
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
