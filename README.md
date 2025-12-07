# Bot SeaTalk para Análise de Dados da Shopee

Este projeto implementa um bot para SeaTalk que se integra com o Google Sheets para fornecer análises de dados de vendas da Shopee. O bot é capaz de responder a perguntas em linguagem natural, como "qual a quantidade total de smartphones?" ou "quais são os top 10 produtos?", e retornar as respostas diretamente no chat do SeaTalk.

## Funcionalidades

- **Integração com SeaTalk**: Recebe mensagens e envia respostas através da API do SeaTalk.
- **Leitura de Google Sheets**: Conecta-se a uma planilha Google Sheets para ler os dados de vendas em tempo real.
- **Análise de Dados com Pandas**: Utiliza a biblioteca `pandas` para realizar cálculos e análises, como:
  - Cálculo de quantidade total (geral ou por produto).
  - Cálculo de média ponderada.
  - Geração de resumos por produto ou período.
  - Identificação de "top N" produtos.
  - Busca por produtos específicos.
  - Estatísticas descritivas de colunas.
- **Processamento de Linguagem Natural (Simples)**: Interpreta perguntas comuns dos usuários para acionar as análises correspondentes.
- **Servidor Flask**: Expõe um endpoint de webhook para a comunicação com o SeaTalk.
- **Configuração Flexível**: Utiliza variáveis de ambiente para facilitar a configuração de credenciais e outros parâmetros.

## Estrutura do Projeto

```
/shopee_seatalk_bot
|-- bot.py                    # Aplicação principal Flask (servidor do bot)
|-- config.py                 # Módulo de configuração
|-- data_analyzer.py          # Lógica de análise de dados com Pandas
|-- question_processor.py     # Processador de perguntas do usuário
|-- seatalk_client.py         # Cliente para a API do SeaTalk
|-- sheets_client.py          # Cliente para a API do Google Sheets
|-- requirements.txt          # Dependências do Python
|-- .env.example              # Arquivo de exemplo para variáveis de ambiente
|-- README.md                 # Este arquivo
```

## Guia de Instalação e Configuração

Siga os passos abaixo para configurar e executar o bot em seu ambiente.

### 1. Pré-requisitos

- Python 3.8 ou superior.
- Conta no SeaTalk com permissões de administrador para criar um app.
- Conta no Google Cloud Platform (GCP) para configurar a API do Google Sheets.
- Uma planilha no Google Sheets com os dados da Shopee.

### 2. Instalação das Dependências

Clone o repositório e instale as bibliotecas Python necessárias:

```bash
git clone <URL_DO_REPOSITORIO> # (simulado)
cd shopee_seatalk_bot
pip install -r requirements.txt
```

### 3. Configuração do SeaTalk

1.  **Crie um App no SeaTalk**: Acesse a [Plataforma de Desenvolvedores do SeaTalk](https://open.seatalk.io/) e crie um novo aplicativo.
2.  **Obtenha as Credenciais**: Anote o **App ID: ODg1Njg0ODk3MjEz** e o **App Secret:Lb4f8c3mRkcKY60LEDtPEX6sQeesMDEj**.
3.  **Configure o Bot**: Na seção "Bot", ative o bot e configure um nome para ele.
4.  **Eventos e Callbacks**: Na seção "Event Subscriptions", você precisará de uma URL pública para o seu bot. Após iniciar o bot (passo 6), use uma ferramenta como `ngrok` para expor sua porta local (`5000` por padrão) e obter uma URL pública (ex: `https://seunome.ngrok.io`).
5.  **Configure a URL de Callback**: Insira a URL pública seguida de `/callback` (ex: `https://seunome.ngrok.io/callback`) no campo "Request URL". O SeaTalk fará uma verificação enviando um `challenge`.
6.  **Token de Verificação**: Crie um token de verificação seguro (qualquer string) e anote-o. Você o usará na configuração do ambiente.

### 4. Configuração do Google Sheets

1.  **Crie um Projeto no GCP**: Acesse o [Google Cloud Console](https://console.cloud.google.com/) e crie um novo projeto.
2.  **Ative as APIs**: No seu projeto, ative a **Google Sheets API** e a **Google Drive API**.
3.  **Crie uma Conta de Serviço**: Vá para "Credentials" -> "Create Credentials" -> "Service Account". Dê um nome à conta e conceda a ela o papel de "Editor" (ou mais restrito, se preferir).
4.  **Gere uma Chave JSON**: Após criar a conta de serviço, vá para a aba "Keys" -> "Add Key" -> "Create new key". Escolha o formato **JSON** e o arquivo será baixado. Renomeie este arquivo para `credentials.json` e coloque-o na raiz do projeto.
5.  **Compartilhe a Planilha**: Abra o arquivo `credentials.json` e copie o email da conta de serviço (campo `client_email`). Vá até sua planilha no Google Sheets, clique em "Share" e cole este email, dando permissão de "Editor".
6.  **Obtenha o ID da Planilha**: O ID da sua planilha está na URL. Por exemplo, em `https://docs.google.com/spreadsheets/d/ESTE_E_O_ID/edit`, copie o valor correspondente.

### 5. Configuração do Ambiente

Crie um arquivo `.env` na raiz do projeto (copiando o `.env.example`) e preencha com as credenciais obtidas:

```ini
# SeaTalk Configuration
SEATALK_APP_ID=seu_app_id_aqui
SEATALK_APP_SECRET=seu_app_secret_aqui
SEATALK_CALLBACK_TOKEN=seu_token_de_verificacao_aqui

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEET_ID=seu_id_da_planilha_aqui

# Server Configuration
HOST=0.0.0.0
PORT=5000
DEBUG=True
```

### 6. Execução do Bot

Com tudo configurado, inicie o servidor Flask:

```bash
python bot.py
```

Se tudo estiver correto, você verá mensagens indicando que o bot foi iniciado com sucesso. Use o `ngrok` para expor a porta local e finalize a configuração do callback no SeaTalk.

## Como Usar o Bot

Após adicionar o bot a um chat no SeaTalk, você pode interagir com ele enviando mensagens. Digite `ajuda` para ver a lista completa de comandos disponíveis.

**Exemplos de Comandos:**

- `quantidade total`
- `quantidade total smartphone xiaomi`
- `top 5 produtos`
- `buscar notebook gamer`
- `estatísticas da coluna preço`
- `colunas`
- `recarregar dados`

## Como Testar Localmente

Você pode testar o processamento de perguntas sem precisar do SeaTalk, enviando requisições para o endpoint `/test`:

```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"question": "qual a quantidade total?"}' \
http://127.0.0.1:5000/test
```
ngrok http 5000 -> Inicia o Server
python bot.py -> Inicia o Robo
