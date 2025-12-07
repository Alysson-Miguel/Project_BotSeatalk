"""
Cliente para integração com SeaTalk Open Platform API
"""
import requests
from typing import Dict
from flask import Flask, request, jsonify
from config import Config

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
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                return data["app_access_token"]
            else:
                raise Exception(f"Erro ao obter bot token: {data}")
        except Exception as e:
            raise Exception(f"Erro bot_access_token: {e}")

    # ============================================================
    #  ENVIAR TEXTO DIRETO
    # ============================================================
    def send_message(self, employee_code: str, message: str):
        token = self.get_bot_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "employee_code": employee_code,
            "message": {
                "tag": "text",
                "text": {
                    "content": message
                }
            }
        }
        resp = requests.post(Config.SEATALK_SEND_MESSAGE_URL, headers=headers, json=payload)
        return resp.json()

    # ============================================================
    #  ENVIAR MARKDOWN
    # ============================================================
    def send_markdown_message(self, employee_code: str, content: str) -> Dict:
        token = self.get_bot_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
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
        resp = requests.post(Config.SEATALK_SEND_MESSAGE_URL, headers=headers, json=payload)
        return resp.json()

    # ============================================================
    #  ENVIAR MENSAGEM EM GRUPO
    # ============================================================
    def send_group_message(self, group_id: str, message_id: str, message: str, sender_id: str):
        """
        Envia mensagem em grupo mencionando o usuário com <mention-tag>
        """
        token = self.get_bot_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

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

        resp = requests.post(
            "https://openapi.seatalk.io/messaging/v2/group_chat",
            headers=headers,
            json=payload
        )
        return resp.json()


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
