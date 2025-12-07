"""
Cliente para integração com Groq API
"""
from groq import Groq
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GroqClient:
    """Cliente para comunicação com a API do Groq"""
    
    def __init__(self, api_key: str):
        """
        Inicializa o cliente Groq
        
        Args:
            api_key: API key do Groq
        """
        self.api_key = api_key
        self.client = Groq(api_key=api_key)
        
        # Usar Llama 3.1 70B (rápido e poderoso)
        self.model = "llama-3.3-70b-versatile"
        
        logger.info("✅ Cliente Groq inicializado com sucesso")
    
    def generate_response(
        self, 
        question: str, 
        context: Optional[str] = None,
        max_tokens: int = 500
    ) -> str:
        """
        Gera uma resposta usando Groq
        
        Args:
            question: Pergunta do usuário
            context: Contexto adicional (dados do sheets, etc)
            max_tokens: Número máximo de tokens na resposta
            
        Returns:
            Resposta gerada pela IA
        """
        try:
            # Monta o prompt
            prompt = self._build_prompt(question, context)
            
            # Gera resposta
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            
            return chat_completion.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta com Groq: {str(e)}")
            return "❌ Desculpe, não consegui processar sua pergunta no momento."
    
    def _build_prompt(self, question: str, context: Optional[str] = None) -> str:
        """
        Constrói o prompt para o Groq
        
        Args:
            question: Pergunta do usuário
            context: Contexto adicional
            
        Returns:
            Prompt formatado
        """
        base_prompt = """Você é um assistente inteligente da Shopee que ajuda funcionários 
com análise de dados e informações da empresa.

Seja sempre:
- Direto e objetivo
- Profissional mas amigável
- Use emojis quando apropriado
- Formate respostas longas com bullet points
- Responda em português brasileiro
- As vezes seja um pouco sarcastico

"""
        
        if context:
            base_prompt += f"\nContexto disponível:\n{context}\n"
        
        base_prompt += f"\nPergunta do usuário: {question}\n\nResposta:"
        
        return base_prompt
    
    def analyze_with_data(
        self, 
        question: str, 
        dataframe_summary: str,
        sample_data: str
    ) -> str:
        """
        Analisa uma pergunta complexa usando dados do Google Sheets
        
        Args:
            question: Pergunta do usuário
            dataframe_summary: Resumo do dataframe (colunas, tipos, etc)
            sample_data: Amostra de dados
            
        Returns:
            Análise gerada pela IA
        """
        context = f"""
Dados disponíveis:
{dataframe_summary}

Amostra dos dados:
{sample_data}
"""
        
        return self.generate_response(question, context, max_tokens=800)
    
    def should_use_ai(self, question: str) -> bool:
        """
        Determina se a pergunta deve ser processada pela IA
        
        Args:
            question: Pergunta do usuário
            
        Returns:
            True se deve usar IA, False caso contrário
        """
        # Palavras-chave que indicam perguntas complexas
        complex_keywords = [
            'por que', 'porque', 'explique', 'como funciona',
            'qual a diferença', 'compare', 'análise',
            'sugestão', 'recomenda', 'o que você acha',
            'me ajude', 'não entendi', 'dúvida',
            'quem', 'o que é', 'como'
        ]
        
        question_lower = question.lower()
        
        # Verifica se contém palavras-chave complexas
        for keyword in complex_keywords:
            if keyword in question_lower:
                return True
        
        # Perguntas muito curtas provavelmente são simples (mas "quem sou eu" deve usar IA)
        if len(question.split()) <= 3 and not any(word in question_lower for word in ['quem', 'o que', 'como']):
            return False
        
        # Perguntas longas podem ser complexas
        if len(question.split()) > 15:
            return True
        
        return False