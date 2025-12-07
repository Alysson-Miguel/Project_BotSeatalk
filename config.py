"""
Módulo de configuração do bot SeaTalk para Shopee
"""
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


class Config:
    """Classe de configuração centralizada"""
    
    # SeaTalk Configuration
    SEATALK_APP_ID = os.getenv('SEATALK_APP_ID', '')
    SEATALK_APP_SECRET = os.getenv('SEATALK_APP_SECRET', '')
    SEATALK_CALLBACK_TOKEN = os.getenv('SEATALK_CALLBACK_TOKEN', '')
    
    # Google Sheets Configuration
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '')
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # SeaTalk API URLs
    SEATALK_TOKEN_URL = "https://openapi.seatalk.io/auth/app_access_token"
    SEATALK_SEND_MESSAGE_URL = "https://openapi.seatalk.io/messaging/v2/single_chat"
    #SEATALK_SEND_TEXT_URL = "https://openapi.seatalk.io/messaging/v2/single_chat"
    
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

    
    @classmethod
    def validate(cls):
        """Valida se as configurações essenciais estão presentes"""
        required_configs = [
            ('SEATALK_APP_ID', cls.SEATALK_APP_ID),
            ('SEATALK_APP_SECRET', cls.SEATALK_APP_SECRET),
            ('GOOGLE_SHEET_ID', cls.GOOGLE_SHEET_ID),
        ]
        
        missing = [name for name, value in required_configs if not value]
        
        if missing:
            raise ValueError(f"Configurações obrigatórias faltando: {', '.join(missing)}")
        
        return True
