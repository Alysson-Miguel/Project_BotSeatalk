"""
Bot SeaTalk para análise de dados da Shopee com IA
"""
from flask import Flask, request, jsonify
import logging
import pprint
import json
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
        logger.info("Inicializando clientes...")
        
        # Groq (obrigatório)
        if Config.GROQ_API_KEY:
            logger.info("Inicializando Groq AI client...")
            groq_client = GroqClient(Config.GROQ_API_KEY)
            logger.info("✅ Groq inicializado!")
        else:
            logger.warning("⚠️ GROQ_API_KEY não configurada - IA desabilitada")
        
        # Sheets (opcional)
        try:
            logger.info("Inicializando Google Sheets client...")
            sheets_client = SheetsClient()
            
            logger.info("Inicializando Question Processor...")
            question_processor = QuestionProcessor(sheets_client)
            logger.info("✅ Sheets e Processor inicializados!")
        except Exception as e:
            logger.warning(f"⚠️ Sheets não disponível: {str(e)}")
        
        logger.info("✅ Sistema inicializado!")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar clientes: {str(e)}", exc_info=True)
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
        # Log do request completo
        logger.info("=" * 60)
        logger.info("📨 CALLBACK RECEBIDO")
        logger.info("=" * 60)
        
        # Log dos headers
        logger.info("Headers:")
        for key, value in request.headers.items():
            logger.info(f"  {key}: {value}")
        
        # Log do body raw
        raw_data = request.get_data(as_text=True)
        logger.info(f"\nBody RAW:\n{raw_data}")
        
        # Tentar parsear JSON
        try:
            data = request.json
            if not data:
                logger.error("❌ Data vazio ou None")
                return jsonify({'error': 'Empty data'}), 400
            
            logger.info(f"\nBody PARSED:\n{pprint.pformat(data, indent=2)}")
        except Exception as json_error:
            logger.error(f"❌ Erro ao parsear JSON: {json_error}")
            return jsonify({'error': 'Invalid JSON'}), 400

        # Challenger (verificação do webhook)
        if data.get('event_type') == 'event_verification':
            challenge = data.get('event', {}).get('seatalk_challenge')
            logger.info(f"🔐 Challenge recebido: {challenge}")
            if challenge:
                response = {'seatalk_challenge': challenge}
                logger.info(f"✅ Respondendo challenge: {response}")
                return jsonify(response), 200
            logger.error("❌ Challenge não encontrado no evento")
            return jsonify({'error': 'Desafio não encontrado'}), 400

        # Mensagem direta
        if data.get('event_type') == 'message_from_bot_subscriber':
            logger.info("💬 Processando mensagem direta...")
            event = data.get('event', {})
            process_direct_message(event)
            return jsonify({'status': 'ok'}), 200

        # Mensagem em grupo (menção)
        if data.get('event_type') == 'new_mentioned_message_received_from_group_chat':
            logger.info("👥 Processando mensagem de grupo...")
            event = data.get('event', {})
            process_group_message(event)
            return jsonify({'status': 'ok'}), 200

        # Evento desconhecido
        logger.warning(f"⚠️ Evento desconhecido: {data.get('event_type')}")
        return jsonify({'status': 'ok', 'message': 'Event type not handled'}), 200

    except Exception as e:
        logger.error(f"❌ ERRO NO CALLBACK: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# ============================================================
# PROCESSAMENTO DE MENSAGENS
# ============================================================
def process_direct_message(event: dict):
    try:
        employee_code = event.get('employee_code')
        message_text = event.get('message', {}).get('text', {}).get('content', '')

        if not employee_code or not message_text:
            logger.warning("⚠️ Mensagem direta incompleta")
            return

        logger.info(f"💬 [DIRETO] De: {employee_code}")
        logger.info(f"💬 [DIRETO] Mensagem: {message_text}")
        
        response = process_question(message_text)
        send_direct_response(employee_code, response)

    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem direta: {str(e)}", exc_info=True)

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
            logger.warning("⚠️ Mensagem de grupo incompleta")
            return

        logger.info(f"👥 [GRUPO] ID: {group_id}")
        logger.info(f"👥 [GRUPO] De: {employee_code}")
        logger.info(f"👥 [GRUPO] Mensagem: {message_text}")

        response = process_question(message_text)
        send_group_response(group_id, message_id, response, sender_id)

    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem de grupo: {str(e)}", exc_info=True)

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
        logger.error(f"❌ Erro ao processar pergunta: {str(e)}", exc_info=True)
        return f"❌ Erro ao processar sua mensagem: {str(e)}"

def send_direct_response(employee_code: str, message: str):
    try:
        logger.info(f"📤 Enviando resposta para {employee_code}...")
        if any(m in message for m in ['**', '```', '•', '#', '\n']):
            result = seatalk_client.send_markdown_message(employee_code, message)
        else:
            result = seatalk_client.send_message(employee_code, message)
        logger.info(f"✅ Resposta enviada:\n{pprint.pformat(result)}")
    except Exception as e:
        logger.error(f"❌ Erro ao enviar resposta direta: {str(e)}", exc_info=True)

def send_group_response(group_id: str, message_id: str, message: str, sender_id: str):
    try:
        logger.info(f"📤 Enviando para grupo {group_id}...")
        result = seatalk_client.send_group_message(group_id, message_id, message, sender_id)
        logger.info(f"✅ Resposta grupo enviada:\n{pprint.pformat(result)}")
    except Exception as e:
        logger.error(f"❌ Erro ao enviar resposta de grupo: {str(e)}", exc_info=True)

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
        logger.error(f"❌ Erro IA: {str(e)}", exc_info=True)
        return previous or "❌ Erro IA."

# ============================================================
# MAIN
# ============================================================
def main():
    try:
        logger.info("🚀 Iniciando Bot SeaTalk...")
        logger.info("=" * 60)
        initialize_clients()
        logger.info("=" * 60)
        logger.info(f"🌐 Servidor rodando em {Config.HOST}:{Config.PORT}")
        logger.info("=" * 60)
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar bot: {str(e)}", exc_info=True)

if __name__ == '__main__':
    main()