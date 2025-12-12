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
        
        explicacao = self.explicar_indicador(question)
        if explicacao:
            return explicacao
        
        # Comandos de ajuda
        if any(cmd in question_lower for cmd in ['help', 'comandos', 'ajuda']):
            return self._get_help_message()
        
        # Listar colunas disponíveis
        if any(cmd in question_lower for cmd in ['colunas', 'columns', 'campos', 'fields']):
            return self._list_columns()
        
        # ===== COMANDOS PARA ABA PRINCIPAL =====
        
        # Prévia dos dados / Indicadores
        if any(cmd in question_lower for cmd in ['!indicadores', '!indicador', '!performance', '!table']):
            return self._show_data_preview()
        
        # ===== COMANDOS PARA ABA SECUNDÁRIA =====
        
        # Prévia da aba secundária
        if any(cmd in question_lower for cmd in ['!Leftover', '!sobras', '!leftover']): # Ainda da mais uma palavra pra leftover
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
• `!Indicadores` - Mostra como está o status dos Indicadores.
• `Explicar [Indicador]`
• `Quais indicadores existem?` - Mostra todos os Indicadores do SITE

**Leftover:**
• `!Leftover` - Mostra dados da segunda aba
• `!Sobras` - Alias para aba secundária

**Informações:**
• `!Ofensores` - Lista maiores ofensores
• `!Fora do target` - Indicadores fora do target
• `status` - Status de todas as abas

**Utilitários:**
• `recarregar` - Atualiza dados do Google Sheets
• `colunas` - Lista colunas disponíveis
• `ajuda` - Mostra esta mensagem

**Exemplo de uso:**
_"!Indicadores"_  
_"!Sobras"_
_"status"_
"""
    
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
    
    def _get_total_quantity(self, question: str) -> str:
        """Calcula quantidade total (usa aba principal por padrão)"""
        analyzer = self.analyzer_main
        
        if not analyzer:
            return "❌ Aba principal não disponível"
        
        try:
            product_name = self._extract_product_name(question)
            total = analyzer.get_total_quantity(product_name)
            if product_name:
                return f"📦 **Quantidade total de '{product_name}':** {total:,.0f}"
            else:
                return f"📦 **Quantidade total geral:** {total:,.0f}"
        except Exception as e:
            logger.error(f"Erro em _get_total_quantity: {e}", exc_info=True)
            return f"❌ Erro ao calcular quantidade total: {str(e)}"
    
    def _get_weighted_average(self, question: str) -> str:
        analyzer = self.analyzer_main
        if not analyzer:
            return "❌ Aba principal não disponível"
        
        try:
            columns = analyzer.get_column_names()
            value_col = None
            weight_col = None
            
            for col in columns:
                if col.lower() in question.lower():
                    if not value_col:
                        value_col = col
                    elif not weight_col:
                        weight_col = col
            
            if not value_col or not weight_col:
                return "❌ Especifique as colunas para calcular a média ponderada.\nEx: 'média ponderada de preço por quantidade'"
            
            avg = analyzer.get_weighted_average(value_col, weight_col)
            return f"📊 **Média ponderada de '{value_col}' por '{weight_col}':** {avg:,.2f}"
        
        except Exception as e:
            logger.error(f"Erro em _get_weighted_average: {e}", exc_info=True)
            return f"❌ Erro ao calcular média ponderada: {str(e)}"
    
    def _get_top_products(self, question: str) -> str:
        analyzer = self.analyzer_main
        if not analyzer:
            return "❌ Aba principal não disponível"
        
        try:
            n = self._extract_number(question) or 10
            top_products = analyzer.get_top_products(n)
            
            if top_products.empty:
                return "❌ Nenhum produto encontrado."
            
            product_col = analyzer._find_product_column()
            qty_col = [col for col in top_products.columns if 'quant' in col.lower()][0]
            
            response = f"🏆 **Top {n} Produtos:**\n\n"
            for idx, row in top_products.iterrows():
                response += f"{idx + 1}. **{row[product_col]}**: {row[qty_col]:,.0f}\n"
            
            return response
        
        except Exception as e:
            logger.error(f"Erro em _get_top_products: {e}", exc_info=True)
            return f"❌ Erro ao obter top produtos: {str(e)}"
    
    def _search_product(self, question: str) -> str:
        analyzer = self.analyzer_main
        if not analyzer:
            return "❌ Aba principal não disponível"
        
        try:
            product_name = self._extract_product_name(question)
            
            if not product_name:
                return "❌ Especifique o nome do produto.\nEx: 'buscar notebook'"
            
            results = analyzer.search_product(product_name)
            
            if results.empty:
                return f"❌ Nenhum produto encontrado com '{product_name}'."
            
            qty_col = [col for col in results.columns if 'quant' in col.lower()][0]
            total_qty = results[qty_col].sum()
            
            formatted = self._format_dataframe(results.head(5))
            
            response = (
                f"🔍 **Resultados para '{product_name}':**\n\n"
                f"• **Total de registros:** {len(results)}\n"
                f"• **Quantidade total:** {total_qty:,.0f}\n\n"
                f"```\n{formatted}\n```"
            )
            return response
        
        except Exception as e:
            logger.error(f"Erro em _search_product: {e}", exc_info=True)
            return f"❌ Erro ao buscar produto: {str(e)}"
    
    def _get_statistics(self, question: str) -> str:
        analyzer = self.analyzer_main
        if not analyzer:
            return "❌ Aba principal não disponível"
        
        try:
            columns = analyzer.get_column_names()
            column_name = next((col for col in columns if col.lower() in question.lower()), None)
            
            if not column_name:
                column_name = next(col for col in columns if 'quant' in col.lower())
            
            stats = analyzer.get_statistics(column_name)
            
            response = (
                f"📊 **Estatísticas de '{column_name}':**\n\n"
                f"• **Total:** {stats['total']:,.2f}\n"
                f"• **Média:** {stats['média']:,.2f}\n"
                f"• **Mediana:** {stats['mediana']:,.2f}\n"
                f"• **Mínimo:** {stats['mínimo']:,.2f}\n"
                f"• **Máximo:** {stats['máximo']:,.2f}\n"
                f"• **Desvio Padrão:** {stats['desvio_padrão']:,.2f}\n"
                f"• **Contagem:** {stats['contagem']}\n"
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Erro em _get_statistics: {e}", exc_info=True)
            return f"❌ Erro ao calcular estatísticas: {str(e)}"
    
    def _get_product_summary(self) -> str:
        analyzer = self.analyzer_main
        if not analyzer:
            return "❌ Aba principal não disponível"
        
        try:
            summary = analyzer.get_summary_by_product()
            
            if summary.empty:
                return "❌ Nenhum dado disponível."
            
            product_col = analyzer._find_product_column()
            qty_col = [col for col in summary.columns if 'quant' in col.lower()][0]
            
            response = "📊 **Resumo por Produto:**\n\n"
            for idx, row in summary.head(10).iterrows():
                response += f"• **{row[product_col]}**: {row[qty_col]:,.0f}\n"
            
            if len(summary) > 10:
                response += f"\n_... e mais {len(summary) - 10} produtos_"
            
            return response
        
        except Exception as e:
            logger.error(f"Erro em _get_product_summary: {e}", exc_info=True)
            return f"❌ Erro ao gerar resumo: {str(e)}"
    
    def _get_default_response(self, question: str) -> str:
        return f"""
                ❓ Desculpe, não entendi sua pergunta: "{question}"

                Digite **ajuda** para ver os comandos disponíveis.
                """
                
    
# ======================================================================
    #  Explicação de Indicadores
    # ======================================================================
    def explicar_indicador(self, message_text: str):
        import logging
        logging.info("🟦 explicar_indicador() foi chamado!")

        text_low = message_text.lower()

        # Verifica se o usuário pediu explicação
        if "explica" not in text_low and "lógica" not in text_low and "logica" not in text_low:
            logging.info("🟨 Não é pedido de explicação.")
            return None

        logging.info("🟧 Pedido de explicação detectado.")

        try:
            logging.info("🔎 Buscando aba 'logica' no Google Sheets...")
            df = self.sheets_client.get_all_data("logica")

            logging.info("🟦 DEBUG — DF LOGICA:")
            logging.info(df)

            if df is None or df.empty:
                logging.error("❌ DF 'logica' vazio")
                return "⚠️ Não consegui carregar a aba 'Logica indicadores'."

            coluna_nome = df.columns[0]
            coluna_logica = df.columns[1]

            logging.info(f"🟩 DEBUG — Nome da coluna de indicadores: {coluna_nome}")
            logging.info(f"🟩 DEBUG — Nome da coluna de lógica: {coluna_logica}")

            indicadores = df[coluna_nome].astype(str).str.lower().tolist()
            logging.info(f"🟨 DEBUG — Indicadores encontrados: {indicadores}")

            encontrado = None
            for ind in indicadores:
                if ind in text_low:
                    encontrado = ind
                    break

            logging.info(f"🟪 DEBUG — Indicador encontrado: {encontrado}")

            if not encontrado:
                return "📘 Qual indicador você deseja que eu explique?"

            linha = df.loc[df[coluna_nome].str.lower() == encontrado]

            logging.info(f"🟥 DEBUG — Linha encontrada: {linha}")

            logica = linha.iloc[0][coluna_logica]

            return (
                f"📘 **Explicação do indicador: {linha.iloc[0][coluna_nome]}**\n\n"
                f"{logica}"
            )

        except Exception as e:
            logging.error(f"❌ Erro explicar_indicador: {e}")
            return f"❌ Erro ao consultar lógica dos indicadores: {e}"
        
            # ======================================================================
    #  Explicação e listagem de indicadores
    # ======================================================================
    def explicar_indicador(self, message_text: str):
        import logging
        text_low = message_text.lower()

        # ------------------------------------------------------------------
        # LISTAR TODOS OS NOMES DOS INDICADORES
        # ------------------------------------------------------------------
        if "quais indicadores" in text_low or \
           "listar indicadores" in text_low or \
           "todos os indicadores" in text_low and "explica" not in text_low:
            
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
        if "explica todos" in text_low or \
           "explicar todos" in text_low or \
           "explicação de todos" in text_low:
            
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