"""
Configuração da aplicação BolãoFácil
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configurações padrão"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database/bolao.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # WhatsApp
    WHATSAPP_API_TOKEN = os.environ.get('WHATSAPP_API_TOKEN')
    WHATSAPP_PHONE_ID = os.environ.get('WHATSAPP_PHONE_ID')
    
    # JWT
    JWT_SECRET = os.environ.get('JWT_SECRET') or 'jwt-secret-key'
    JWT_ALGORITHM = 'HS256'
    
    # Configurações gerais
    ITEMS_PER_PAGE = 10
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
