#!/usr/bin/env python3
"""
Script de teste para verificar as correções implementadas
"""
import logging
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_logging_configuration():
    """Testa se o logging não está duplicando"""
    print("🧪 Testando configuração de logging...")
    
    # Importa o app (que configura o logging)
    from app import logger
    
    # Verifica quantos handlers existem
    root_logger = logging.getLogger()
    handler_count = len(root_logger.handlers)
    
    print(f"📊 Número de handlers: {handler_count}")
    
    if handler_count <= 2:  # Normalmente 1 ou 2 é normal
        print("✅ Logging configurado corretamente (sem duplicação)")
        return True
    else:
        print("❌ Possível duplicação de logging detectada")
        return False

def test_question_processor_methods():
    """Testa se os métodos duplicados foram removidos"""
    print("\n🧪 Testando métodos do QuestionProcessor...")
    
    try:
        from Functions.question_processor import QuestionProcessor
        
        # Verifica se métodos antigos foram removidos
        methods = dir(QuestionProcessor)
        
        removed_methods = [
            '_get_total_quantity',
            '_get_top_products', 
            '_search_product',
            '_get_product_summary'
        ]
        
        found_old_methods = [method for method in removed_methods if method in methods]
        
        if found_old_methods:
            print(f"❌ Métodos antigos ainda presentes: {found_old_methods}")
            return False
        
        # Verifica se novos métodos existem
        new_methods = [
            '_get_indicators_out_of_target',
            '_get_worst_indicators'
        ]
        
        missing_new_methods = [method for method in new_methods if method not in methods]
        
        if missing_new_methods:
            print(f"❌ Novos métodos não encontrados: {missing_new_methods}")
            return False
        
        print("✅ Métodos do QuestionProcessor atualizados corretamente")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar QuestionProcessor: {e}")
        return False

def test_duplicate_callback_removed():
    """Testa se o callback duplicado foi removido"""
    print("\n🧪 Testando remoção de callback duplicado...")
    
    try:
        # Lê o arquivo seatalk_client.py
        with open('Functions/seatalk_client.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verifica se não há mais callback duplicado
        problematic_patterns = [
            '@app.route("/callback"',
            'def callback():',
            'app = Flask(__name__)'
        ]
        
        found_patterns = [pattern for pattern in problematic_patterns if pattern in content]
        
        if found_patterns:
            print(f"❌ Ainda há código de callback duplicado: {found_patterns}")
            return False
        
        print("✅ Callback duplicado removido com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar callback: {e}")
        return False

def test_ai_prompt_update():
    """Testa se o prompt da IA foi atualizado"""
    print("\n🧪 Testando prompt da IA...")
    
    try:
        from AI.groq_client import GroqClient
        
        # Cria uma instância fake para testar o prompt
        client = GroqClient("fake_key")
        prompt = client._build_prompt("teste", "contexto teste")
        
        # Verifica se contém palavras-chave do novo prompt
        keywords = ["indicadores", "performance", "KPIs", "e-commerce"]
        found_keywords = [kw for kw in keywords if kw.lower() in prompt.lower()]
        
        if len(found_keywords) >= 2:
            print("✅ Prompt da IA atualizado para contexto de indicadores")
            return True
        else:
            print("❌ Prompt da IA não foi atualizado adequadamente")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar IA: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes das correções implementadas...\n")
    
    tests = [
        test_logging_configuration,
        test_question_processor_methods,
        test_duplicate_callback_removed,
        test_ai_prompt_update
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erro no teste {test.__name__}: {e}")
            results.append(False)
    
    print(f"\n📊 Resumo dos testes:")
    print(f"✅ Sucessos: {sum(results)}")
    print(f"❌ Falhas: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 Todas as correções foram implementadas com sucesso!")
        print("🔥 O problema de mensagens duplicadas foi RESOLVIDO!")
    else:
        print("\n⚠️ Algumas correções podem precisar de ajustes.")

if __name__ == "__main__":
    main()