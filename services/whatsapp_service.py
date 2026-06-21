import logging

import requests
from flask import current_app


logger = logging.getLogger(__name__)


class WhatsAppService:
    @staticmethod
    def send_message(phone, message):
        api_url = current_app.config.get("WHATSAPP_API_URL")
        api_token = current_app.config.get("WHATSAPP_API_TOKEN")

        if not api_url or not api_token:
            logger.info("WhatsApp não configurado. Mensagem para %s: %s", phone, message)
            return {"sent": False, "fallback": "log"}

        response = requests.post(
            api_url,
            json={"to": phone, "message": message},
            headers={"Authorization": f"Bearer {api_token}"},
            timeout=10,
        )
        response.raise_for_status()
        return {"sent": True, "status_code": response.status_code}
