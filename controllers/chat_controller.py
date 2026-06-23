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
    lower_text = text.lower()
    bot_reply = "Desculpe, não entendi. Você pode perguntar sobre 'próximos jogos', seu 'ranking', 'palpites' ou 'regras'."
    
    if re.search(r'\b(ajuda|regras|como funciona)\b', lower_text):
        bot_reply = "O Bola Fácil é um bolão de futebol! Você ganha 10 pts acertando o placar exato, 5 pts acertando vencedor+gols, 3 pts acertando só o vencedor, e 2 pts acertando um empate (com gols diferentes)."
    
    elif re.search(r'\b(ranking|pontos|minha posi|classificação)\b', lower_text):
        from models.user import Pool
        pool = Pool.get_default()
        if pool:
            ranking = Score.get_ranking(pool["id"])
            user_rank = next((r for r in ranking if r["user_id"] == current_user.id), None)
            if user_rank:
                bot_reply = f"Você está com {user_rank['total_points']} pontos no ranking atual!"
            else:
                bot_reply = "Você ainda não pontuou no bolão principal."
        else:
            bot_reply = "Não encontrei o bolão principal para verificar seu ranking."
            
    elif re.search(r'\b(jogos|próximos|hoje)\b', lower_text):
        from models.user import Pool
        pool = Pool.get_default()
        games = Game.list(pool["id"]) if pool else []
        upcoming = [g for g in games if g["status"] == "scheduled"]
        if upcoming:
            g = upcoming[0]
            from utils.helpers import format_match_time
            time = format_match_time(g["match_datetime"])
            bot_reply = f"O próximo jogo é {g['home_team']} x {g['away_team']} no dia {time['date']} às {time['time']}."
        else:
            bot_reply = "Não há jogos agendados no momento."
            
    elif re.search(r'\b(palpite|palpitar|aposta)\b', lower_text):
        bot_reply = "Para palpitar, acesse a página de Jogos, escolha uma partida que ainda não começou e clique em 'Palpitar'. Boa sorte!"
    
    ChatMessage.send_private(0, current_user.id, bot_reply, is_bot=1)
    
    return jsonify({"success": True, "reply": bot_reply})

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
