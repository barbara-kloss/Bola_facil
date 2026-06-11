"""
Controlador de Integração WhatsApp
"""

from flask import Blueprint, request, jsonify
from services.whatsapp_service import WhatsAppService

whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/whatsapp')

@whatsapp_bp.route('/webhook', methods=['POST'])
def webhook():
    """Webhook para receber mensagens do WhatsApp"""
    data = request.get_json()
    
    # TODO: Processar mensagem recebida
    
    return jsonify({'status': 'received'})

@whatsapp_bp.route('/send', methods=['POST'])
def send_message():
    """Enviar mensagem via WhatsApp"""
    data = request.get_json()
    phone = data.get('phone')
    message = data.get('message')
    
    # TODO: Enviar mensagem usando WhatsAppService
    
    return jsonify({'message': 'Mensagem enviada'})
