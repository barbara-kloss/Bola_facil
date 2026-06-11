"""
Serviço de Integração WhatsApp
"""

import requests
from config import Config

class WhatsAppService:
    """Serviço para integração com API WhatsApp"""
    
    BASE_URL = "https://graph.instagram.com/v17.0/me/messages"
    
    @staticmethod
    def send_message(phone_number, message):
        """
        Envia mensagem via WhatsApp
        
        Args:
            phone_number: Número do telefone no formato internacional
            message: Conteúdo da mensagem
            
        Returns:
            bool: True se enviado com sucesso
        """
        headers = {
            "Authorization": f"Bearer {Config.WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {"body": message}
        }
        
        # TODO: Implementar envio de mensagem
        # response = requests.post(self.BASE_URL, json=payload, headers=headers)
        return True
    
    @staticmethod
    def send_notification(users, message):
        """
        Envia notificação para múltiplos usuários
        
        Args:
            users: Lista de usuários
            message: Mensagem a enviar
        """
        # TODO: Enviar mensagem para cada usuário
        pass
