import requests
import time # Importa o módulo time

URL_DO_SEU_WEBHOOK = "https://openapi.seatalk.io/webhook/group/iNCIam_zTSaCzvN8qLp0pg"

# O payload correto para o SeaTalk
payload = {
    "tag": "text",
    "text": {
        "format": 1,
        "content": ""
    }
}


# Define o intervalo em segundos
INTERVALO_SEGUNDOS = 30

print(f"Iniciando o envio de 'Hello World' para o SeaTalk a cada {INTERVALO_SEGUNDOS} segundos...")
#print(f"Webhook URL: {URL_DO_SEU_WEBHOOK}") 
print("Pressione Ctrl+C para parar o script.")

while True: # Loop infinito
    try:
        # Faz a requisição POST com 'json=' para garantir o Content-Type correto
        response = requests.post(URL_DO_SEU_WEBHOOK, json=payload)
        # Verifica se a requisição foi bem-sucedida (código 200)
        response.raise_for_status()

        print(f"\n--- {time.ctime()} ---") # Imprime a hora atual para cada envio
        print(f"Requisição POST para SeaTalk enviada com sucesso.")
        #print(f"Status da Resposta: {response.status_code}")
        #print(f"Conteúdo da Resposta: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"\n--- {time.ctime()} ---") # Imprime a hora atual para cada erro
        print(f"Ocorreu um erro ao fazer a requisição: {e}")
        break

    # Espera o tempo definido antes da próxima iteração
    time.sleep(INTERVALO_SEGUNDOS)