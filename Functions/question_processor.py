"""
Processador de perguntas e comandos do usuário
Suporta múltiplas abas do Google Sheets
"""
import re
import logging
from typing import Optional
import pandas as pd
from Functions.data_analyzer import ShopeeDataAnalyzer
from Functions.sheets_client import SheetsClient
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class QuestionProcessor:
    """Processa perguntas do usuário e retorna respostas baseadas nos dados"""
    
    def __init__(self, sheets_client: SheetsClient):
        """
        Inicializa o processador de perguntas
        
        Args:
            sheets_client: Cliente do Google Sheets
        """
        logger.info("🔧 Inicializando QuestionProcessor...")
        
        # Validação do sheets_client
        if sheets_client is None:
            logger.error("❌ sheets_client é None!")
            raise ValueError("sheets_client não pode ser None")
        
        logger.info(f"✅ sheets_client recebido.") #: {type(sheets_client)}
        
        self.sheets_client = sheets_client
        
        # Analyzers para diferentes abas
        self.analyzer_main = None
        self.analyzer_secondary = None
        
        # Status de prontidão
        self.is_ready_main = False
        self.is_ready_secondary = False
        
        logger.info("📊 Iniciando carregamento de dados...")
        self._load_data()
        
        logger.info(f"🏁 Inicialização concluída.")
        logger.info(f"   Aba principal: {self.is_ready_main}")
        logger.info(f"   Aba secundária: {self.is_ready_secondary}")
    
    # ======================================================================
    #  Carregamento de dados
    # ======================================================================
    
    def _load_data(self):
        """Carrega dados de todas as abas configuradas"""
        # Carregar aba principal
        self._load_main_data()
        
        # Carregar aba secundária
        self._load_secondary_data()
    
    def _load_main_data(self):
        """Carrega dados da aba principal"""
        try:
            logger.info("=" * 60)
            logger.info("📊 CARREGANDO ABA PRINCIPAL")
            logger.info("=" * 60)
            
            df = self.sheets_client.get_all_data('main')
            
            if df is None or df.empty:
                logger.error("❌ Aba principal: sem dados")
                self.analyzer_main = None
                self.is_ready_main = False
                return
            
            logger.info(f"✅ Aba principal carregada: {df.shape[0]} linhas")
            self.analyzer_main = ShopeeDataAnalyzer(df)
            self.is_ready_main = True
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar aba principal: {e}")
            logger.exception("Stack trace:")
            self.analyzer_main = None
            self.is_ready_main = False
    
    def _load_secondary_data(self):
        """Carrega dados da aba secundária"""
        try:
            logger.info("=" * 60)
            logger.info("📊 CARREGANDO ABA SECUNDÁRIA")
            logger.info("=" * 60)
            
            df = self.sheets_client.get_all_data('secondary')
            
            if df is None or df.empty:
                logger.warning("⚠️ Aba secundária: sem dados (não é crítico)")
                self.analyzer_secondary = None
                self.is_ready_secondary = False
                return
            
            logger.info(f"✅ Aba secundária carregada: {df.shape[0]} linhas")
            self.analyzer_secondary = ShopeeDataAnalyzer(df)
            self.is_ready_secondary = True
            
        except Exception as e:
            logger.warning(f"⚠️ Aba secundária não disponível: {e}")
            self.analyzer_secondary = None
            self.is_ready_secondary = False
    
    def refresh_data(self, sheet: str = 'all'):
        """
        Recarrega os dados do Google Sheets
        
        Args:
            sheet: 'all', 'main' ou 'secondary'
        """
        logger.info(f"🔄 Recarregando dados: {sheet}")
        
        if sheet in ['all', 'main']:
            self._load_main_data()
        
        if sheet in ['all', 'secondary']:
            self._load_secondary_data()
        
        if sheet == 'all':
            status = []
            if self.is_ready_main:
                status.append("✅ Aba principal OK")
            else:
                status.append("❌ Aba principal falhou")
            
            if self.is_ready_secondary:
                status.append("✅ Aba secundária OK")
            else:
                status.append("⚠️ Aba secundária indisponível")
            
            return "\n".join(status)
        
        is_ready = self.is_ready_main if sheet == 'main' else self.is_ready_secondary
        return f"✅ {sheet} recarregada!" if is_ready else f"❌ Falha ao recarregar {sheet}"
    
    @property
    def is_ready(self):
        """Sistema está pronto se pelo menos a aba principal estiver carregada"""
        return self.is_ready_main

    # ======================================================================
    #  Método auxiliar — FORMATAÇÃO BONITA DA TABELA
    # ======================================================================
    
    def _format_dataframe(self, df: pd.DataFrame) -> str:
        """Formata o DataFrame em colunas alinhadas e limpas."""
        if df is None or df.empty:
            return "❌ DataFrame vazio ou inválido"

        df = df.fillna("-")

        # Ajusta larguras das colunas
        col_widths = {
            col: max(df[col].astype(str).map(len).max(), len(col))
            for col in df.columns
        }

        header = "  ".join(col.ljust(col_widths[col]) for col in df.columns)
        rows = "\n".join(
            "  ".join(str(row[col]).ljust(col_widths[col]) for col in df.columns)
            for _, row in df.iterrows()
        )

        return f"{header}\n{rows}"

    # ======================================================================
    #  Processamento principal das perguntas
    # ======================================================================
    
    def process_question(self, question: str) -> str:
        """
        Processa uma pergunta e retorna a resposta
        
        Args:
            question: Pergunta do usuário
        
        Returns:
            Resposta formatada
        """
        if not self.is_ready:
            logger.warning(f"⚠️ Processador não está pronto.")
            return "❌ Não foi possível carregar os dados. Verifique a configuração do Google Sheets."
        
        question_lower = question.lower().strip()
        
        # Primeiro verifica explicações de indicadores
        explicacao = self.explicar_indicador(question)
        if explicacao:
            return explicacao
        
        # Comandos de ajuda
        if any(cmd in question_lower for cmd in ['help', 'comandos', 'ajuda']):
            return self._get_help_message()
        
        # Listar colunas disponíveis
        if any(cmd in question_lower for cmd in ['colunas', 'columns', 'campos', 'fields']):
            return self._list_columns()
        
        # Status do sistema
        if any(cmd in question_lower for cmd in ['status', 'estado']):
            return self._get_sheets_status()
        
        # ===== COMANDOS PARA ABA PRINCIPAL (INDICADORES) =====
        
        # Prévia dos dados / Indicadores
        if any(cmd in question_lower for cmd in ['!indicadores', '!indicador', '!performance', '!table']):
            return self._show_data_preview()
        
        # Indicadores fora do target
        if any(cmd in question_lower for cmd in ['!fora do target', '!fora target', 'fora do target']):
            return self._get_indicators_out_of_target()
        
        # Maiores ofensores
        if any(cmd in question_lower for cmd in ['!ofensores', 'ofensores', 'piores indicadores']):
            return self._get_worst_indicators()
        
        # ===== COMANDOS PARA ABA SECUNDÁRIA =====
        
        # Prévia da aba secundária
        if any(cmd in question_lower for cmd in ['!leftover', '!sobras', '!leftover']): 
            return self._show_secondary_data_preview()
        
        # ===== COMANDOS GERAIS =====
        # Recarregar dados
        if any(word in question_lower for word in ['recarregar', 'atualizar', 'refresh', 'reload']):
            return self.refresh_data()
                
        # Se não reconhecer o comando
        return self._get_default_response(question)
    

    # ======================================================================
    #  Métodos auxiliares de resposta
    # ======================================================================
    
    def _get_help_message(self) -> str:
        return """
📋 **Comandos Disponíveis:**

**Consultas de Indicadores (Aba Principal):**
• `!Indicadores` - Mostra status dos Indicadores de Performance
• `!Fora do target` - Indicadores que estão fora do target
• `!Ofensores` - Lista maiores ofensores (piores indicadores)
• `Explicar [Indicador]` - Explica a lógica de um indicador específico
• `Quais indicadores existem?` - Lista todos os indicadores disponíveis
• `Explica todos` - Mostra explicação de todos os indicadores

**Leftover:**
• `!Leftover` - Mostra dados da segunda aba (sobras)
• `!Sobras` - Alias para aba secundária

**Informações do Sistema:**
• `status` - Status de todas as abas e conexões
• `colunas` - Lista colunas disponíveis
• `recarregar` - Atualiza dados do Google Sheets
• `ajuda` - Mostra esta mensagem

**Exemplo de uso:**
_"!Indicadores"_  
_"!Fora do target"_
_"Explicar GMV"_
_"status"_
"""
    
    def _get_indicators_out_of_target(self) -> str:
        """Retorna indicadores que estão fora do target"""
        if not self.analyzer_main:
            return "❌ Aba principal não disponível"
        
        try:
            df = self.analyzer_main.df
            
            # Procura por colunas que indicam target ou status
            target_cols = [col for col in df.columns if any(word in col.lower() 
                          for word in ['target', 'meta', 'objetivo', 'status', 'resultado'])]
            
            if not target_cols:
                return "⚠️ Não encontrei colunas de target/status nos dados"
            
            # Filtra indicadores fora do target (assumindo que há uma coluna de status)
            status_col = target_cols[0]  # Usa a primeira coluna encontrada
            
            # Procura por valores que indicam "fora do target"
            out_of_target = df[df[status_col].astype(str).str.contains(
                'vermelho|red|fora|ruim|baixo|crítico', case=False, na=False)]
            
            if out_of_target.empty:
                return "✅ **Todos os indicadores estão dentro do target!**"
            
            formatted = self._format_dataframe(out_of_target)
            return f"🚨 **Indicadores Fora do Target:**\n```\n{formatted}\n```"
            
        except Exception as e:
            logger.error(f"Erro em _get_indicators_out_of_target: {e}", exc_info=True)
            return f"❌ Erro ao buscar indicadores fora do target: {str(e)}"
    
    def _get_worst_indicators(self) -> str:
        """Retorna os piores indicadores (maiores ofensores)"""
        if not self.analyzer_main:
            return "❌ Aba principal não disponível"
        
        try:
            df = self.analyzer_main.df
            
            # Procura por colunas numéricas que podem indicar performance
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if not numeric_cols:
                # Se não há colunas numéricas, mostra baseado em status
                status_cols = [col for col in df.columns if any(word in col.lower() 
                              for word in ['status', 'resultado', 'performance'])]
                
                if status_cols:
                    status_col = status_cols[0]
                    worst = df[df[status_col].astype(str).str.contains(
                        'vermelho|red|crítico|ruim', case=False, na=False)]
                    
                    if worst.empty:
                        return "✅ **Nenhum indicador crítico encontrado!**"
                    
                    formatted = self._format_dataframe(worst.head(10))
                    return f"🔴 **Indicadores Críticos:**\n```\n{formatted}\n```"
                
                return "⚠️ Não consegui identificar indicadores problemáticos"
            
            # Se há colunas numéricas, ordena pela primeira (assumindo que menor é pior)
            main_metric = numeric_cols[0]
            worst = df.nsmallest(10, main_metric)
            
            formatted = self._format_dataframe(worst)
            return f"📉 **Top 10 Piores Indicadores (por {main_metric}):**\n```\n{formatted}\n```"
            
        except Exception as e:
            logger.error(f"Erro em _get_worst_indicators: {e}", exc_info=True)
            return f"❌ Erro ao buscar piores indicadores: {str(e)}"
    
    def _get_sheets_status(self) -> str:
        """Retorna o status de todas as abas"""
        main_status = "✅ OK" if self.is_ready_main else "❌ Falhou"
        secondary_status = "✅ OK" if self.is_ready_secondary else "⚠️ Indisponível"
        
        main_info = ""
        if self.analyzer_main and self.is_ready_main:
            df = self.analyzer_main.df
            main_info = f" ({df.shape[0]} linhas, {df.shape[1]} colunas)"
        
        secondary_info = ""
        if self.analyzer_secondary and self.is_ready_secondary:
            df = self.analyzer_secondary.df
            secondary_info = f" ({df.shape[0]} linhas, {df.shape[1]} colunas)"
        
        return f"""
                    📊 **Status das Abas:**

                    • **Aba Principal:** {main_status}{main_info}
                    • **Aba Secundária:** {secondary_status}{secondary_info}

                    Sistema: {"✅ Pronto" if self.is_ready else "❌ Não pronto"}
                    """
    
    def _list_columns(self) -> str:
        """Lista colunas de ambas as abas"""
        response = []
        
        if self.analyzer_main:
            columns_main = self.analyzer_main.get_column_names()
            columns_list = "\n".join([f"  • {col}" for col in columns_main])
            response.append(f"📊 **Colunas da Aba Principal:**\n{columns_list}")
        
        if self.analyzer_secondary:
            columns_sec = self.analyzer_secondary.get_column_names()
            columns_list = "\n".join([f"  • {col}" for col in columns_sec])
            response.append(f"\n📊 **Colunas da Aba Secundária:**\n{columns_list}")
        
        return "\n".join(response) if response else "❌ Nenhuma aba disponível"
    
    def _show_data_preview(self) -> str:
        """Mostra prévia da aba principal"""
        if not self.analyzer_main:
            return "❌ Aba principal não disponível"

        # Buscar valor da célula Filter!B1 de forma correta
        b1_value = self.sheets_client.get_cell_value("Filter!B1")
        b1_value = b1_value if b1_value else "N/A"

        # Buscar preview da aba principal
        df = self.analyzer_main.get_data_preview(24)
        formatted = self._format_dataframe(df)

        # Montar retorno
        return (
            f"📋 **Indicadores Performance SITE**\n"
            f"📌 *Resumo do dia: **{b1_value}**\n"
            f"```\n{formatted}\n```"
        )
        
    
    def _show_secondary_data_preview(self) -> str:
        """Mostra prévia da aba secundária"""
        if not self.analyzer_secondary:
            return "❌ Aba secundária não disponível. Configure GOOGLE_SHEET_RANGE_2 no .env"
        
        df = self.analyzer_secondary.get_data_preview(24)
        formatted = self._format_dataframe(df)
        ontem = datetime.now() - timedelta(days=1)
        ontem_formatado = ontem.strftime("%d-%m-%y")
        return f"📋 **Resumo Leftover {ontem_formatado}**\n```\n{formatted}\n```"
    
    def _get_default_response(self, question: str) -> str:
        return f"""
❓ Desculpe, não entendi sua pergunta: "{question}"

Digite **ajuda** para ver os comandos disponíveis.

💡 **Dicas rápidas:**
• `!Indicadores` - Ver status dos indicadores
• `!Fora do target` - Ver indicadores problemáticos  
• `Explicar [nome do indicador]` - Entender um indicador
"""
                
    
    # ======================================================================
    #  Explicação e listagem de indicadores
    # ======================================================================
    def explicar_indicador(self, message_text: str):
        import logging
        text_low = message_text.lower()

        # ------------------------------------------------------------------
        # LISTAR TODOS OS NOMES DOS INDICADORES
        # ------------------------------------------------------------------
        if ("quais indicadores" in text_low or 
            "listar indicadores" in text_low or 
            "todos os indicadores" in text_low) and "explica" not in text_low:
            
            logging.info("📋 Pedido para listar todos os indicadores.")
            
            df = self.sheets_client.get_all_data("logica")
            if df is None or df.empty:
                return "⚠️ Não consegui carregar a aba 'Logica indicadores'."

            col_nome = df.columns[0]
            indicadores = df[col_nome].tolist()

            lista_formatada = "\n".join([f"• {i}" for i in indicadores])

            return f"📋 **Lista de Indicadores Disponíveis:**\n\n{lista_formatada}"

        # ------------------------------------------------------------------
        # EXPLICAR TODOS OS INDICADORES
        # ------------------------------------------------------------------
        if ("explica todos" in text_low or 
            "explicar todos" in text_low or 
            "explicação de todos" in text_low):
            
            logging.info("📘 Pedido para explicar TODOS os indicadores.")
            
            df = self.sheets_client.get_all_data("logica")
            if df is None or df.empty:
                return "⚠️ Não consegui carregar a aba 'Logica indicadores'."

            col_nome = df.columns[0]
            col_logica = df.columns[1]

            resposta = "📘 **Explicação de Todos os Indicadores**\n\n"

            for _, row in df.iterrows():
                nome = row[col_nome]
                logica = row[col_logica]

                resposta += f"🔹 **{nome}**\n{logica}\n\n" + "—" * 40 + "\n\n"

            return resposta

        # ------------------------------------------------------------------
        # EXPLICAR INDICADOR ESPECÍFICO
        # ------------------------------------------------------------------
        if "explica" not in text_low and "lógica" not in text_low and "logica" not in text_low:
            return None  # não é pedido de explicação

        logging.info("📘 Pedido de explicação individual detectado.")

        try:
            df = self.sheets_client.get_all_data("logica")
            if df is None or df.empty:
                return "⚠️ Não consegui carregar a aba 'Logica indicadores'."

            col_nome = df.columns[0]
            col_logica = df.columns[1]

            indicadores = df[col_nome].astype(str).str.lower().tolist()

            encontrado = None
            for ind in indicadores:
                if ind in text_low:
                    encontrado = ind
                    break

            if not encontrado:
                return "📘 Qual indicador você deseja que eu explique?"

            linha = df.loc[df[col_nome].str.lower() == encontrado]
            logica = linha.iloc[0][col_logica]

            return (
                f"📘 **Explicação do indicador: {linha.iloc[0][col_nome]}**\n\n"
                f"{logica}"
            )

        except Exception as e:
            logging.error(f"❌ Erro explicar_indicador: {e}")
            return f"❌ Erro ao consultar lógica dos indicadores: {e}"




    
    # ======================================================================
    # Métodos de extração
    # ======================================================================
    
    def _extract_product_name(self, text: str) -> Optional[str]:
        keywords = ['quantidade', 'total', 'buscar', 'procurar', 'produto', 'de', 'do', 'da']
        words = text.lower().split()
        filtered_words = [w for w in words if w not in keywords and len(w) > 2]
        return ' '.join(filtered_words) if filtered_words else None
    
    def _extract_number(self, text: str) -> Optional[int]:
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else None