"""
Bot SeaTalk para análise de dados da Shopee com IA
"""
from flask import Flask, request, jsonify
import logging
import pprint
import json
from config import Config
from Functions.seatalk_client import SeaTalkClient
from Functions.sheets_client import SheetsClient
from Functions.question_processor import QuestionProcessor
from AI.groq_client import GroqClient
import os

# ==================================
# CONFIG LOGGING COM PRETTY PRINT (SEM DUPLICAÇÃO)
# ==================================
class PrettyFormatter(logging.Formatter):
    def format(self, record):
        if isinstance(record.msg, dict):
            record.msg = pprint.pformat(record.msg, indent=2)
        return super().format(record)

# Configura logging apenas se ainda não foi configurado
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    for handler in logging.getLogger().handlers:
        handler.setFormatter(PrettyFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger(__name__)

# =====================================
# INICIALIZAÇÃO
# =====================================
app = Flask(__name__)
seatalk_client = SeaTalkClient()
sheets_client = None
question_processor = None
groq_client = None

def initialize_clients():
    global sheets_client, question_processor, groq_client
    try:
        logger.info("=" * 60)
        logger.info("🚀 INICIALIZANDO CLIENTES")
        logger.info("=" * 60)
        
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
            logger.info(f"📊 Sheets client criado: {sheets_client is not None}")
            
            logger.info("➕ Registrando aba de lógica dos indicadores...")
            sheets_client.add_sheet_range(
                key="logica",
                range_name="Logica indicadores!A1:B29"
            )
            logger.info("✅ Aba 'logica' registrada!")
            
            logger.info("Inicializando Question Processor...")
            question_processor = QuestionProcessor(sheets_client)
            logger.info(f"🔍 Question Processor criado: {question_processor is not None}")
            
            # === DIAGNÓSTICO DETALHADO DOS ANALYZERS ===
            logger.info("🧪 Verificando analyzer_main:")
            if question_processor.analyzer_main:
                df = question_processor.analyzer_main.df
                logger.info(f"📋 DataFrame MAIN existe: {df is not None}")
                if df is not None:
                    logger.info(f"📊 Shape: {df.shape}")
                    logger.info(f"📊 Colunas: {list(df.columns)}")
            else:
                logger.error("❌ analyzer_main é None!")

            logger.info("🧪 Verificando analyzer_secondary:")
            if question_processor.analyzer_secondary:
                df2 = question_processor.analyzer_secondary.df
                logger.info(f"📋 DataFrame SECONDARY existe: {df2 is not None}")
                if df2 is not None:
                    logger.info(f"📊 Shape: {df2.shape}")
                    logger.info(f"📊 Colunas: {list(df2.columns)}")
            else:
                logger.warning("⚠️ analyzer_secondary é None!")
            
            logger.info("=" * 60)
            
            if question_processor.is_ready:
                logger.info("✅ Sheets e Processor PRONTOS!")
            else:
                logger.error("❌ Processor NÃO está pronto!")
                
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Sheets: {str(e)}", exc_info=True)
            logger.error(f"❌ Stack trace completo:", exc_info=True)
        
        logger.info("=" * 60)
        logger.info("✅ Sistema inicializado!")
        logger.info("=" * 60)
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar clientes: {str(e)}", exc_info=True)
        return False

# ============================================================
# ROTAS
# ============================================================
@app.route('/health', methods=['GET'])
def health_check():
    processor_ready = question_processor.is_ready if question_processor else False
    return jsonify({
        'status': 'ok',
        'message': 'Bot SeaTalk está funcionando',
        'ai_enabled': groq_client is not None,
        'sheets_enabled': sheets_client is not None,
        'processor_ready': processor_ready
    }), 200

@app.route('/callback', methods=['POST'])
def callback():
    try:
        logger.info("=" * 60)
        logger.info("📨 CALLBACK RECEBIDO")
        logger.info("=" * 60)
        
        # Verifica se é realmente JSON
        if not request.is_json:
            logger.error(f"❌ Não é JSON! Content-Type: {request.content_type}")
            logger.error(f"Raw data: {request.get_data(as_text=True)}")
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        # Força parsing do JSON
        try:
            data = request.get_json(force=True)
            #logger.info(f"📦 Dados recebidos:\n{pprint.pformat(data)}")
        except Exception as e:
            logger.error(f"❌ Erro ao parsear JSON: {e}")
            logger.error(f"Raw data: {request.get_data(as_text=True)}")
            return jsonify({'error': 'Invalid JSON format'}), 400

        # Challenger (verificação do webhook)
        if data.get('event_type') == 'event_verification':
            challenge = data.get('event', {}).get('seatalk_challenge')
            logger.info(f"🔐 Challenge recebido: {challenge}")
            if challenge:
                response = {'status': 'ok'}
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
        logger.info(f"📦 Event completo:\n{pprint.pformat(event)}")
        
        employee_code = event.get('employee_code')
        
        # Tenta pegar o sender_id também
        sender = event.get('sender', {})
        sender_id = sender.get('seatalk_id')
        
        message_text = event.get('message', {}).get('text', {}).get('content', '')

        logger.info(f"👤 Employee Code: {employee_code}")
        logger.info(f"👤 Sender ID: {sender_id}")
        logger.info(f"💬 Mensagem: {message_text}")

        if not message_text:
            logger.warning("⚠️ Mensagem direta sem texto")
            return

        # Tenta usar sender_id se employee_code não funcionar
        target_id = employee_code or sender_id
        
        if not target_id:
            logger.error("❌ Não foi possível identificar o destinatário!")
            return

        logger.info(f"💬 [DIRETO] De: {target_id}")
        logger.info(f"💬 [DIRETO] Mensagem: {message_text}")
        
        response = process_question(message_text)
        send_direct_response(target_id, response)

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
        logger.info(f"👥 [GRUPO] De: {employee_code} (Sender: {sender_id})")
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
        logger.info(f"🤔 Processando pergunta: '{message_text}'")
        logger.info(f"📊 Processor ready: {question_processor.is_ready if question_processor else 'N/A'}")
        
        # Verifica se deve usar IA ANTES de processar
        use_ai_for_complex = groq_client and groq_client.should_use_ai(message_text)
        
        if question_processor and question_processor.is_ready:
            logger.info("✅ Usando question_processor")
            response = question_processor.process_question(message_text)
            
            # Só usa IA se a resposta indica que não entendeu OU se é pergunta complexa
            if should_fallback_to_ai(response):
                logger.info("🤖 Fazendo fallback para IA (não entendeu)")
                response = generate_ai_response(message_text, response)
            elif use_ai_for_complex and not response.startswith("📋") and not response.startswith("📊"):
                # Só usa IA para perguntas complexas se não foi uma resposta de dados estruturados
                logger.info("🤖 Usando IA para pergunta complexa")
                response = generate_ai_response(message_text, None)
                
        elif question_processor:
            logger.warning("⚠️ Processor existe mas não está pronto")
            response = "⌛ Ainda estou carregando os dados. Tente novamente em instantes."
        else:
            logger.error("❌ Processor não existe")
            response = "❌ Bot não está configurado corretamente."

        logger.info(f"📤 Resposta gerada: {response[:100]}...")
        return response

    except Exception as e:
        logger.error(f"❌ Erro ao processar pergunta: {str(e)}", exc_info=True)
        return f"❌ Erro ao processar sua mensagem: {str(e)}"
 
def send_direct_response(target_id: str, message: str):
    try:
        logger.info(f"📤 Enviando resposta para {target_id}...")
        logger.info(f"📝 Mensagem: {message[:100]}...")
        
        if any(m in message for m in ['**', '```', '•', '#', '\n']):
            result = seatalk_client.send_markdown_message(target_id, message)
        else:
            result = seatalk_client.send_message(target_id, message)
        
        logger.info(f"✅ Resultado do envio:\n{pprint.pformat(result)}")
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
        # Usa qualquer analyzer que existir
        analyzer = None
        if question_processor:
            analyzer = question_processor.analyzer_main or question_processor.analyzer_secondary

        if analyzer and analyzer.df is not None:
            df = analyzer.df
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
        
        # Pega a porta do ambiente ou usa 5000 como padrão
        port = int(os.environ.get('PORT', Config.PORT or 10000))
        host = Config.HOST or '0.0.0.0'
        
        logger.info(f"🌐 Servidor rodando em {host}:{port}")
        logger.info("=" * 60)
        
        app.run(
            host=host,
            port=port,
            debug=Config.DEBUG
        )
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar bot: {str(e)}", exc_info=True)

if __name__ == '__main__':
    main()