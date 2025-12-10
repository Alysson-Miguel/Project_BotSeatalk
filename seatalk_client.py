"""
Cliente para integração com SeaTalk Open Platform API
"""
import requests
import logging
from typing import Dict
from flask import Flask, request, jsonify
from config import Config

logger = logging.getLogger(__name__)

class SeaTalkClient:
    """Cliente para comunicação com a API do SeaTalk"""

    def __init__(self):
        self.app_id = Config.SEATALK_APP_ID
        self.app_secret = Config.SEATALK_APP_SECRET
        self.access_token = None
        self.token_expires_at = 0

    # ============================================================
    #  TOKEN
    # ============================================================
    def get_bot_access_token(self):
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        try:
            response = requests.post(
                "https://openapi.seatalk.io/auth/app_access_token",
                json=payload
            )
            
            # === LOG DE DEBUG ===
            logger.info(f"🔐 Token request - Status: {response.status_code}")
            logger.info(f"🔐 Token request - Content-Type: {response.headers.get('Content-Type')}")
            
            # Verifica se é HTML
            if 'text/html' in response.headers.get('Content-Type', ''):
                logger.error(f"❌ API retornou HTML em vez de JSON!")
                logger.error(f"Response: {response.text[:500]}")
                raise Exception(f"API retornou HTML - Status {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 0:
                logger.info("✅ Token obtido com sucesso")
                return data["app_access_token"]
            else:
                raise Exception(f"Erro ao obter bot token: {data}")
                
        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"❌ Resposta não é JSON!")
            logger.error(f"Status: {response.status_code}")
            logger.error(f"Content-Type: {response.headers.get('Content-Type')}")
            logger.error(f"Body: {response.text[:1000]}")
            raise Exception(f"API retornou resposta inválida: {e}")
        except Exception as e:
            logger.error(f"❌ Erro ao obter token: {e}")
            raise

    # ============================================================
    #  HELPER PARA FAZER REQUESTS COM VALIDAÇÃO
    # ============================================================
    def _make_request(self, url: str, payload: Dict, token: str) -> Dict:
        """Helper para fazer requests com validação adequada"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"📤 Enviando para: {url}")
            #logger.info(f"📦 Payload: {payload}")
            
            resp = requests.post(url, headers=headers, json=payload)
            
            # === LOGS DETALHADOS ===
            logger.info(f"📊 Status Code: {resp.status_code}")
            #logger.info(f"📋 Headers: {dict(resp.headers)}")
            logger.info(f"📄 Content-Type: {resp.headers.get('Content-Type')}")
            
            # Verifica se é HTML (ERRO!)
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                logger.error(f"❌ API RETORNOU HTML!")
                logger.error(f"URL: {url}")
                logger.error(f"Status: {resp.status_code}")
                logger.error(f"Response: {resp.text[:1000]}")
                
                return {
                    'error': 'API retornou HTML',
                    'status_code': resp.status_code,
                    'url': url,
                    'response_preview': resp.text[:500]
                }
            
            # Verifica status HTTP
            if resp.status_code >= 400:
                logger.error(f"❌ Erro HTTP {resp.status_code}")
                logger.error(f"Response: {resp.text}")
            
            # Tenta parsear JSON
            try:
                result = resp.json()
                logger.info(f"✅ Resposta JSON: {result}")
                return result
            except requests.exceptions.JSONDecodeError:
                logger.error(f"❌ Resposta não é JSON válido!")
                logger.error(f"Body: {resp.text[:1000]}")
                return {
                    'error': 'Resposta inválida',
                    'status_code': resp.status_code,
                    'body': resp.text[:500]
                }
                
        except Exception as e:
            logger.error(f"❌ Erro na requisição: {e}", exc_info=True)
            return {'error': str(e)}

    # ============================================================
    #  ENVIAR TEXTO DIRETO
    # ============================================================
    def send_message(self, employee_code: str, message: str):
        token = self.get_bot_access_token()
        
        # URL CORRETA - Verifique na documentação do SeaTalk!
        url = "https://openapi.seatalk.io/messaging/v2/single_chat"
        
        payload = {
            "employee_code": employee_code,
            "message": {
                "tag": "text",
                "text": {
                    "content": message
                }
            }
        }
        
        return self._make_request(url, payload, token)

    # ============================================================
    #  ENVIAR MARKDOWN
    # ============================================================
    def send_markdown_message(self, employee_code: str, content: str) -> Dict:
        token = self.get_bot_access_token()
        
        url = "https://openapi.seatalk.io/messaging/v2/single_chat"
        
        payload = {
            "employee_code": employee_code,
            "message": {
                "tag": "text",
                "text": {
                    "format": 1,  # ativa markdown
                    "content": content
                }
            }
        }
        
        return self._make_request(url, payload, token)

    # ============================================================
    #  ENVIAR MENSAGEM EM GRUPO
    # ============================================================
    def send_group_message(self, group_id: str, message_id: str, message: str, sender_id: str):
        token = self.get_bot_access_token()
        
        url = "https://openapi.seatalk.io/messaging/v2/group_chat"
        
        content = f"<mention-tag target=\"seatalk://user?id={sender_id}\"/>{message}"

        payload = {
            "group_id": group_id,
            "quoted_message_id": message_id,
            "message": {
                "tag": "text",
                "text": {
                    "content": content
                }
            }
        }

        return self._make_request(url, payload, token)


# ============================================================
#  CALLBACK FLASK (fora da classe)
# ============================================================
app = Flask(__name__)

@app.route("/callback", methods=["POST"])
def callback():
    data = request.json
    print("Callback recebido:", data)

    # Challenger verification
    if data.get("event_type") == "event_verification":
        if data.get("token") == Config.SEATALK_CALLBACK_TOKEN:
            return jsonify({"seatalk_challenge": data["event"]["seatalk_challenge"]})
        else:
            return jsonify({"error": "invalid token"}), 403

    # Mensagem mencionada em grupo
    if data.get("event_type") == "new_mentioned_message_received_from_group_chat":
        event = data["event"]
        group_id = event["group_id"]
        sender_id = event["message"]["sender"]["seatalk_id"]
        message_id = event["message"]["message_id"]
        texto = event["message"]["text"]["plain_text"]

        resposta = f"Olá <mention-tag target=\"seatalk://user?id={sender_id}\"/>, estou aqui! 👋"

        client = SeaTalkClient()
        result = client.send_group_message(group_id, message_id, resposta, sender_id)

        print("Resposta enviada:", result)
        return jsonify({"status": "OK"})

    return jsonify({"status": "IGNORED"})