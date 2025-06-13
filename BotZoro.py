import requests
import base64
import time
import os
from datetime import datetime


"""Criado por Alysson & Gemini"""

def send_image_and_text_recurrently(
    webhook_url: str,
    image_path: str,
    text_message: str,
    interval_seconds: int = 15, # Tempo em que será mandado os Reports
    max_iterations: int = None
):
    print(f"Iniciando o envio de imagem e texto para o SeaTalk a cada {interval_seconds} segundos...")
    if max_iterations is not None:
        print(f"Serão feitas no máximo {max_iterations} iterações.")
    else:
        print("Pressione Ctrl+C para parar o script a qualquer momento.")

    iteration_count = 0
    while True:
        try:
            # 1. Preparar e enviar a Imagem
            if not os.path.exists(image_path):
                print(f"Erro: O arquivo de imagem não foi encontrado em: {image_path}. Encerrando.")
                break

            with open(image_path, "rb") as f:
                raw_image_content: bytes = f.read()
                base64_encoded_image: str = base64.b64encode(raw_image_content).decode("latin-1")
            # Aqui carregamos nossa mensagem
            image_payload = {
                "tag": "image",
                "image_base64": {
                    "content": base64_encoded_image
                }
            }

            print(f"\n--- {time.ctime()} (Iteração {iteration_count + 1}) ---")
            print("Enviando imagem...")
            response_image = requests.post(url=webhook_url, json=image_payload)
            response_image.raise_for_status()
            print(f"Status da Imagem: {response_image.status_code}")

            # Pequena pausa para garantir que o webhook processe a primeira requisição
            time.sleep(1)

            # 2. Preparar e enviar o Texto
            timestamp = datetime.now().strftime("%H:%M") # Atualiza o timestamp a cada iteração
            formatted_text_message = f"{text_message} {timestamp}"

            text_payload = {
                "tag": "text",
                "text": {
                    "format": 1,
                    "content": formatted_text_message
                }
            }

            print("Enviando texto...")
            response_text = requests.post(url=webhook_url, json=text_payload)
            response_text.raise_for_status()
            print(f"Status do Texto: {response_text.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"\n--- {time.ctime()} ---")
            print(f"Ocorreu um erro na requisição: {e}")
            break 
        except FileNotFoundError:
            print(f"\n--- {time.ctime()} ---")
            print(f"Erro: Arquivo de imagem não encontrado em '{image_path}'. Verifique o caminho.")
            break
        except Exception as e:
            print(f"\n--- {time.ctime()} ---")
            print(f"Ocorreu um erro inesperado: {e}")
            break
        except KeyboardInterrupt:
            print("\nScript interrompido manualmente (Ctrl+C).")
            break

        iteration_count += 1
        if max_iterations is not None and iteration_count >= max_iterations:
            print(f"\nLimite de {max_iterations} iterações alcançado. Encerrando.")
            break


        time.sleep(interval_seconds)

# --- Exemplo de Uso ---
if __name__ == "__main__":
    # Sua URL de webhook
    MY_WEBHOOK_URL = "https://openapi.seatalk.io/webhook/group/iNCIam_zTSaCzvN8qLp0pg"
    # O caminho para a imagem de exemplo
    IMAGE_TO_SEND = "Report_Example.png" 


    send_image_and_text_recurrently(
        webhook_url=MY_WEBHOOK_URL,
        image_path=IMAGE_TO_SEND,
        text_message="Overview Example",
        interval_seconds=15
    )
