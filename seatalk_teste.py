    def send_markdown_message(self, user_id: str, content: str) -> Dict:
        """Envia mensagem em markdown"""

        token = self.get_bot_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "receiver": [{
                "type": 1,
                "id": user_id
            }],
            "message": {
                "tag": "text",
                "text": {
                    "content": content
                }
            }
        }

        try:
            response = requests.post(
                Config.SEATALK_SEND_MESSAGE_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao enviar markdown: {str(e)}")