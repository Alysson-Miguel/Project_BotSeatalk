"""
Processador de perguntas e comandos do usuário
"""
import re
import logging
from typing import Optional
from data_analyzer import ShopeeDataAnalyzer
from sheets_client import SheetsClient

logger = logging.getLogger(__name__)


class QuestionProcessor:
    """Processa perguntas do usuário e retorna respostas baseadas nos dados"""
    
    def __init__(self, sheets_client: SheetsClient):
        """
        Inicializa o processador de perguntas
        
        Args:
            sheets_client: Cliente do Google Sheets
        """
        self.sheets_client = sheets_client
        self.analyzer = None
        self.is_ready = False
        self._load_data()
    
    def _load_data(self):
        """Carrega dados do Google Sheets"""
        try:
            logger.info("📊 Iniciando carregamento de dados do Sheets...")
            df = self.sheets_client.get_all_data()
            
            if df is None:
                logger.error("❌ get_all_data() retornou None")
                self.analyzer = None
                self.is_ready = False
                return
            
            logger.info(f"📋 DataFrame recebido: {df.shape[0]} linhas, {df.shape[1]} colunas")
            
            if df.empty:
                logger.warning("⚠️ DataFrame está vazio!")
                self.analyzer = None
                self.is_ready = False
                return
            
            logger.info("🔧 Criando ShopeeDataAnalyzer...")
            self.analyzer = ShopeeDataAnalyzer(df)
            self.is_ready = True
            logger.info("✅ Dados carregados com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados: {str(e)}", exc_info=True)
            self.analyzer = None
            self.is_ready = False
    
    def refresh_data(self):
        """Recarrega os dados do Google Sheets"""
        logger.info("🔄 Recarregando dados...")
        self._load_data()
        return "✅ Dados recarregados com sucesso!" if self.is_ready else "❌ Falha ao recarregar dados."
    
    def process_question(self, question: str) -> str:
        """
        Processa uma pergunta e retorna a resposta
        
        Args:
            question: Pergunta do usuário
        
        Returns:
            Resposta formatada
        """
        if not self.is_ready:
            logger.warning(f"⚠️ Processador não está pronto. Analyzer: {self.analyzer is not None}")
            return "❌ Não foi possível carregar os dados. Verifique a configuração do Google Sheets."
        
        question_lower = question.lower().strip()
        
        # Comandos de ajuda
        if any(cmd in question_lower for cmd in ['help', 'comandos', 'ajuda']):
            return self._get_help_message()
        
        # Listar colunas disponíveis
        if any(cmd in question_lower for cmd in ['colunas', 'columns', 'campos', 'fields']):
            return self._list_columns()
        
        # Prévia dos dados
        if any(cmd in question_lower for cmd in ['prévia', 'preview', 'mostrar dados', 'show data']):
            return self._show_data_preview()
        
        # Quantidade total
        if any(word in question_lower for word in ['quantidade total', 'total de quantidade', 'soma quantidade']):
            return self._get_total_quantity(question)
        
        # Média ponderada
        if any(word in question_lower for word in ['média ponderada', 'weighted average', 'ponderada']):
            return self._get_weighted_average(question)
        
        # Top produtos
        if any(word in question_lower for word in ['top', 'maiores', 'principais', 'melhores']):
            return self._get_top_products(question)
        
        # Buscar produto
        if any(word in question_lower for word in ['buscar', 'procurar', 'search', 'find', 'produto']):
            return self._search_product(question)
        
        # Estatísticas
        if any(word in question_lower for word in ['estatística', 'stats', 'resumo', 'summary']):
            return self._get_statistics(question)
        
        # Resumo por produto
        if any(word in question_lower for word in ['resumo por produto', 'agrupar por produto', 'group by product']):
            return self._get_product_summary()
        
        # Recarregar dados
        if any(word in question_lower for word in ['recarregar', 'atualizar', 'refresh', 'reload']):
            return self.refresh_data()
        
        # Se não reconhecer o comando
        return self._get_default_response(question)
    
    # ---------------------- Métodos auxiliares ----------------------
    
    def _get_help_message(self) -> str:
        return """
📋 **Comandos Disponíveis:**

**Consultas de Dados:**
• `quantidade total` - Mostra a quantidade total geral
• `quantidade total [produto]` - Mostra quantidade de um produto específico
• `top 10` ou `top 5` - Mostra os produtos com maior quantidade
• `buscar [produto]` - Busca informações de um produto
• `estatísticas [coluna]` - Mostra estatísticas de uma coluna
• `resumo por produto` - Mostra resumo agrupado por produto

**Informações:**
• `colunas` - Lista todas as colunas disponíveis
• `prévia` - Mostra as primeiras linhas dos dados

**Utilitários:**
• `recarregar` - Atualiza os dados do Google Sheets
• `ajuda` - Mostra esta mensagem

**Exemplo de uso:**
_"quantidade total smartphone"_  
_"top 10"_  
_"buscar notebook"_
"""
    
    def _list_columns(self) -> str:
        columns = self.analyzer.get_column_names()
        columns_list = "\n".join([f"• {col}" for col in columns])
        return f"📊 **Colunas disponíveis:**\n\n{columns_list}"
    
    def _show_data_preview(self) -> str:
        preview = self.analyzer.get_data_preview(5)
        return f"📋 **Prévia dos dados (5 primeiras linhas):**\n\n```\n{preview.to_string()}\n```"
    
    def _get_total_quantity(self, question: str) -> str:
        try:
            product_name = self._extract_product_name(question)
            total = self.analyzer.get_total_quantity(product_name)
            if product_name:
                return f"📦 **Quantidade total de '{product_name}':** {total:,.0f}"
            else:
                return f"📦 **Quantidade total geral:** {total:,.0f}"
        except Exception as e:
            logger.error(f"Erro em _get_total_quantity: {e}", exc_info=True)
            return f"❌ Erro ao calcular quantidade total: {str(e)}"
    
    def _get_weighted_average(self, question: str) -> str:
        try:
            columns = self.analyzer.get_column_names()
            value_col = None
            weight_col = None
            for col in columns:
                if col.lower() in question.lower():
                    if not value_col:
                        value_col = col
                    elif not weight_col:
                        weight_col = col
            if not value_col or not weight_col:
                return "❌ Por favor, especifique as colunas para calcular a média ponderada.\nExemplo: 'média ponderada de preço por quantidade'"
            avg = self.analyzer.get_weighted_average(value_col, weight_col)
            return f"📊 **Média ponderada de '{value_col}' por '{weight_col}':** {avg:,.2f}"
        except Exception as e:
            logger.error(f"Erro em _get_weighted_average: {e}", exc_info=True)
            return f"❌ Erro ao calcular média ponderada: {str(e)}"
    
    def _get_top_products(self, question: str) -> str:
        try:
            n = self._extract_number(question) or 10
            top_products = self.analyzer.get_top_products(n)
            if top_products.empty:
                return "❌ Nenhum produto encontrado."
            response = f"🏆 **Top {n} Produtos:**\n\n"
            for idx, row in top_products.iterrows():
                product_col = self.analyzer._find_product_column()
                qty_col = [col for col in top_products.columns if 'quant' in col.lower()][0]
                response += f"{idx + 1}. **{row[product_col]}**: {row[qty_col]:,.0f}\n"
            return response
        except Exception as e:
            logger.error(f"Erro em _get_top_products: {e}", exc_info=True)
            return f"❌ Erro ao obter top produtos: {str(e)}"
    
    def _search_product(self, question: str) -> str:
        try:
            product_name = self._extract_product_name(question)
            if not product_name:
                return "❌ Por favor, especifique o nome do produto a buscar.\nExemplo: 'buscar notebook'"
            results = self.analyzer.search_product(product_name)
            if results.empty:
                return f"❌ Nenhum produto encontrado com o termo '{product_name}'."
            total_qty = results[[col for col in results.columns if 'quant' in col.lower()][0]].sum()
            response = f"🔍 **Resultados para '{product_name}':**\n\n"
            response += f"• **Total de registros:** {len(results)}\n"
            response += f"• **Quantidade total:** {total_qty:,.0f}\n\n"
            if len(results) <= 5:
                response += "**Detalhes:**\n```\n" + results.to_string() + "\n```"
            else:
                response += f"_Mostrando 5 de {len(results)} registros:_\n```\n" + results.head(5).to_string() + "\n```"
            return response
        except Exception as e:
            logger.error(f"Erro em _search_product: {e}", exc_info=True)
            return f"❌ Erro ao buscar produto: {str(e)}"
    
    def _get_statistics(self, question: str) -> str:
        try:
            columns = self.analyzer.get_column_names()
            column_name = next((col for col in columns if col.lower() in question.lower()), None)
            if not column_name:
                column_name = next(col for col in columns if 'quant' in col.lower())
            stats = self.analyzer.get_statistics(column_name)
            response = f"📊 **Estatísticas de '{column_name}':**\n\n"
            response += f"• **Total:** {stats['total']:,.2f}\n"
            response += f"• **Média:** {stats['média']:,.2f}\n"
            response += f"• **Mediana:** {stats['mediana']:,.2f}\n"
            response += f"• **Mínimo:** {stats['mínimo']:,.2f}\n"
            response += f"• **Máximo:** {stats['máximo']:,.2f}\n"
            response += f"• **Desvio Padrão:** {stats['desvio_padrão']:,.2f}\n"
            response += f"• **Contagem:** {stats['contagem']}\n"
            return response
        except Exception as e:
            logger.error(f"Erro em _get_statistics: {e}", exc_info=True)
            return f"❌ Erro ao calcular estatísticas: {str(e)}"
    
    def _get_product_summary(self) -> str:
        try:
            summary = self.analyzer.get_summary_by_product()
            if summary.empty:
                return "❌ Nenhum dado disponível para resumo."
            response = "📊 **Resumo por Produto:**\n\n"
            for idx, row in summary.head(10).iterrows():
                product_col = self.analyzer._find_product_column()
                qty_col = [col for col in summary.columns if 'quant' in col.lower()][0]
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
    
    def _extract_product_name(self, text: str) -> Optional[str]:
        keywords = ['quantidade', 'total', 'buscar', 'procurar', 'produto', 'de', 'do', 'da']
        words = text.lower().split()
        filtered_words = [w for w in words if w not in keywords and len(w) > 2]
        return ' '.join(filtered_words) if filtered_words else None
    
    def _extract_number(self, text: str) -> Optional[int]:
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else None