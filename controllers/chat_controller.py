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
    
    # Simple simulated bot response for now
    bot_reply = "Anotado! Em breve você poderá registrar apostas por aqui."
    ChatMessage.send_private(0, current_user.id, bot_reply, is_bot=1)
    
    return jsonify({"success": True})

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
