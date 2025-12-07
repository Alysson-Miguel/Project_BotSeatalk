"""
Bot SeaTalk para análise de dados da Shopee com IA
"""
from flask import Flask, request, jsonify
import logging
import pprint
from config import Config
from seatalk_client import SeaTalkClient
from sheets_client import SheetsClient
from question_processor import QuestionProcessor
from groq_client import GroqClient

# ============================================================
# CONFIG LOGGING COM PRETTY PRINT
# ============================================================
class PrettyFormatter(logging.Formatter):
    def format(self, record):
        if isinstance(record.msg, dict):
            record.msg = pprint.pformat(record.msg, indent=2)
        return super().format(record)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

for handler in logging.getLogger().handlers:
    handler.setFormatter(PrettyFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger(__name__)

# ============================================================
# INICIALIZAÇÃO
# ============================================================
app = Flask(__name__)
seatalk_client = SeaTalkClient()
sheets_client = None
question_processor = None
groq_client = None

def initialize_clients():
    global sheets_client, question_processor, groq_client
    try:
        logger.info("Inicializando Google Sheets client...")
        sheets_client = SheetsClient()
        
        logger.info("Inicializando Question Processor...")
        question_processor = QuestionProcessor(sheets_client)
        
        logger.info("Inicializando Groq AI client...")
        groq_client = GroqClient(Config.GROQ_API_KEY)
        
        logger.info("✅ Clientes inicializados com sucesso!")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar clientes: {str(e)}")
        return False

# ============================================================
# ROTAS
# ============================================================
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'Bot SeaTalk está funcionando',
        'ai_enabled': groq_client is not None
    }), 200

@app.route('/callback', methods=['POST'])
def callback():
    try:
        data = request.json
        logger.info("Callback recebido:", data)  # Pretty print aplicado

        # Challenger
        if data.get('event_type') == 'event_verification':
            challenge = data.get('event', {}).get('seatalk_challenge')
            if challenge:
                return jsonify({'seatalk_challenge': challenge}), 200
            return jsonify({'error': 'Desafio não encontrado'}), 400

        # Mensagem direta
        if data.get('event_type') == 'message_from_bot_subscriber':
            event = data.get('event', {})
            process_direct_message(event)

        # Mensagem em grupo (menção)
        if data.get('event_type') == 'new_mentioned_message_received_from_group_chat':
            event = data.get('event', {})
            process_group_message(event)

        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        logger.error(f"Erro no callback: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# PROCESSAMENTO DE MENSAGENS
# ============================================================
def process_direct_message(event: dict):
    try:
        employee_code = event.get('employee_code')
        message_text = event.get('message', {}).get('text', {}).get('content', '')

        if not employee_code or not message_text:
            return

        logger.info(f"💬 [DIRETO] Mensagem de {employee_code}: {message_text}")
        
        response = process_question(message_text)
        send_direct_response(employee_code, response)

    except Exception as e:
        logger.error(f"Erro ao processar mensagem direta: {str(e)}")

def process_group_message(event: dict):
    try:
        group_id = event.get('group_id')
        message = event.get('message', {})

        sender = message.get('sender', {})
        sender_id = sender.get('seatalk_id')
        employee_code = sender.get('employee_code')

        plain_text = message.get('text', {}).get('plain_text', '')
        message_text = plain_text.replace('@RoboCOP', '').strip()

        message_id = message.get('message_id')

        if not group_id or not message_text:
            return

        logger.info(f"👥 [GRUPO] Mensagem de {employee_code} no grupo {group_id}: {message_text}")

        response = process_question(message_text)

        send_group_response(group_id, message_id, response, sender_id)

    except Exception as e:
        logger.error(f"Erro ao processar mensagem de grupo: {str(e)}")

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def process_question(message_text: str) -> str:
    try:
        use_ai_for_complex = groq_client and groq_client.should_use_ai(message_text)

        if question_processor and question_processor.is_ready:
            response = question_processor.process_question(message_text)
            if should_fallback_to_ai(response) or use_ai_for_complex:
                response = generate_ai_response(message_text, response)
        elif question_processor:
            response = "⌛ Ainda estou carregando os dados. Tente novamente em instantes."
        else:
            response = "❌ Bot não está configurado corretamente."

        return response

    except Exception as e:
        logger.error(f"Erro ao processar pergunta: {str(e)}")
        return f"❌ Erro ao processar sua mensagem: {str(e)}"

def send_direct_response(employee_code: str, message: str):
    try:
        if any(m in message for m in ['**', '```', '•', '#', '\n']):
            result = seatalk_client.send_markdown_message(employee_code, message)
        else:
            result = seatalk_client.send_message(employee_code, message)
        logger.info(f"Resposta enviada:\n{pprint.pformat(result)}")
    except Exception as e:
        logger.error(f"Erro ao enviar resposta direta: {str(e)}")

def send_group_response(group_id: str, message_id: str, message: str, sender_id: str):
    try:
        logger.info(f"📤 Enviando para grupo {group_id}...")
        result = seatalk_client.send_group_message(group_id, message_id, message, sender_id)
        logger.info(f"Resposta grupo enviada:\n{pprint.pformat(result)}")
    except Exception as e:
        logger.error(f"Erro ao enviar resposta de grupo: {str(e)}")

def should_fallback_to_ai(response: str) -> bool:
    fallback_indicators = [
        "não encontrei", "não entendi", "não consegui",
        "tente reformular", "não sei", "❓"
    ]
    return any(i in response.lower() for i in fallback_indicators)

def generate_ai_response(question: str, previous: str = None) -> str:
    if not groq_client:
        return previous or "❌ IA não disponível."
    try:
        if question_processor and question_processor.analyzer.df is not None:
            df = question_processor.analyzer.df
            summary = f"Colunas: {', '.join(df.columns)}\nRegistros: {len(df)}"
            sample = df.head(3).to_string()
            response = groq_client.analyze_with_data(question, summary, sample)
        else:
            response = groq_client.generate_response(question)
        return f"🤖 {response}"
    except Exception as e:
        logger.error(f"Erro IA: {str(e)}")
        return previous or "❌ Erro IA."

# ============================================================
# MAIN
# ============================================================
def main():
    try:
        logger.info("Iniciando clientes...")
        initialize_clients()
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
    except Exception as e:
        logger.error(f"Erro ao iniciar bot: {str(e)}")

if __name__ == '__main__':
    main()
