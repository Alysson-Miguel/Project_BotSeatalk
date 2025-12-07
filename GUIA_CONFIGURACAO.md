# Guia Completo de Configuração do Bot SeaTalk para Shopee

Este documento fornece instruções detalhadas para configurar e executar o bot SeaTalk integrado com Google Sheets para análise de dados da Shopee.

## Índice

1. [Configuração do Google Cloud Platform e Google Sheets](#1-configuração-do-google-cloud-platform-e-google-sheets)
2. [Configuração do SeaTalk Open Platform](#2-configuração-do-seatalk-open-platform)
3. [Instalação e Configuração do Bot](#3-instalação-e-configuração-do-bot)
4. [Exposição do Servidor Local (ngrok)](#4-exposição-do-servidor-local-ngrok)
5. [Teste e Validação](#5-teste-e-validação)
6. [Solução de Problemas](#6-solução-de-problemas)

---

## 1. Configuração do Google Cloud Platform e Google Sheets

### 1.1. Criar Projeto no Google Cloud Platform

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Clique em **"Select a project"** no topo da página.
3. Clique em **"New Project"**.
4. Dê um nome ao projeto (ex: "Shopee Bot") e clique em **"Create"**.
5. Aguarde a criação do projeto e selecione-o.

### 1.2. Ativar APIs Necessárias

1. No menu lateral, vá para **"APIs & Services"** > **"Library"**.
2. Procure por **"Google Sheets API"** e clique nela.
3. Clique em **"Enable"**.
4. Repita o processo para **"Google Drive API"**.

### 1.3. Criar Conta de Serviço

1. No menu lateral, vá para **"APIs & Services"** > **"Credentials"**.
2. Clique em **"Create Credentials"** > **"Service Account"**.
3. Preencha os campos:
   - **Service account name**: `shopee-bot-service`
   - **Service account ID**: (gerado automaticamente)
   - **Description**: "Conta de serviço para bot Shopee"
4. Clique em **"Create and Continue"**.
5. Em **"Grant this service account access to project"**, selecione o papel **"Editor"** (ou crie um papel personalizado mais restrito).
6. Clique em **"Continue"** e depois em **"Done"**.

### 1.4. Gerar Chave JSON

1. Na lista de contas de serviço, clique na conta que você acabou de criar.
2. Vá para a aba **"Keys"**.
3. Clique em **"Add Key"** > **"Create new key"**.
4. Selecione o formato **JSON** e clique em **"Create"**.
5. O arquivo JSON será baixado automaticamente. **Renomeie este arquivo para `credentials.json`**.
6. **Importante**: Guarde este arquivo em local seguro e nunca o compartilhe publicamente.

### 1.5. Preparar a Planilha do Google Sheets

1. Crie uma nova planilha no Google Sheets ou abra a planilha existente com os dados da Shopee.
2. Certifique-se de que a primeira linha contém os **cabeçalhos das colunas** (ex: "produto", "quantidade", "preço", "data").
3. Abra o arquivo `credentials.json` que você baixou e copie o valor do campo `client_email` (ex: `shopee-bot-service@seu-projeto.iam.gserviceaccount.com`).
4. Na planilha do Google Sheets, clique em **"Share"** (Compartilhar).
5. Cole o email da conta de serviço e dê permissão de **"Editor"**.
6. Clique em **"Send"**.

### 1.6. Obter ID da Planilha

1. Abra a planilha no navegador.
2. A URL terá o formato: `https://docs.google.com/spreadsheets/d/ID_DA_PLANILHA/edit`
3. Copie o valor de `ID_DA_PLANILHA` (a parte entre `/d/` e `/edit`).

---

## 2. Configuração do SeaTalk Open Platform

### 2.1. Criar Conta e Acessar a Plataforma

1. Acesse [https://open.seatalk.io/](https://open.seatalk.io/).
2. Faça login com sua conta SeaTalk ou crie uma nova conta.
3. Você precisará ter permissões de administrador na sua organização SeaTalk.

### 2.2. Criar um Novo App

1. No painel da plataforma, clique em **"Create App"** ou **"Apps"** > **"Create"**.
2. Preencha as informações do app:
   - **App Name**: "Shopee Data Bot"
   - **Description**: "Bot para análise de dados da Shopee"
   - **App Type**: Selecione **"Bot"**
3. Clique em **"Create"**.

### 2.3. Obter Credenciais do App

1. Após criar o app, você será direcionado para a página de configurações.
2. Anote os seguintes valores:
   - **App ID** (ou Client ID)
   - **App Secret** (ou Client Secret)
3. **Importante**: Mantenha o App Secret em segurança.

### 2.4. Configurar o Bot

1. No menu lateral do app, vá para **"Bot"** ou **"Features"** > **"Bot"**.
2. Ative o bot se ainda não estiver ativo.
3. Configure um **nome** e **descrição** para o bot.

### 2.5. Configurar Event Subscriptions (Callbacks)

**Nota**: Esta etapa será concluída após iniciar o servidor do bot (passo 3).

1. No menu lateral, vá para **"Event Subscriptions"** ou **"Event Callback"**.
2. Você precisará fornecer uma **Request URL** (URL de callback).
3. Esta URL deve ser pública e acessível pela internet (usaremos `ngrok` para isso).
4. O formato da URL será: `https://seu-dominio.ngrok.io/callback`
5. Crie um **Verification Token** (pode ser qualquer string aleatória e segura, ex: `meu_token_secreto_123`). Anote este token.
6. **Aguarde até o passo 4 para finalizar esta configuração**.

### 2.6. Configurar Permissões

1. Vá para **"Permissions"** ou **"Scopes"**.
2. Certifique-se de que as seguintes permissões estão habilitadas:
   - **Send messages** (enviar mensagens)
   - **Receive messages** (receber mensagens)
   - **Read user information** (opcional, se precisar de informações do usuário)

---

## 3. Instalação e Configuração do Bot

### 3.1. Instalar Python e Dependências

1. Certifique-se de ter **Python 3.8 ou superior** instalado:
   ```bash
   python --version
   ```

2. Clone ou baixe o código do bot para uma pasta local.

3. Navegue até a pasta do projeto:
   ```bash
   cd /caminho/para/shopee_seatalk_bot
   ```

4. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

### 3.2. Configurar Variáveis de Ambiente

1. Copie o arquivo de exemplo `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```

2. Abra o arquivo `.env` em um editor de texto e preencha com suas credenciais:

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

3. **Importante**: Substitua os valores de exemplo pelos valores reais obtidos nos passos anteriores.

### 3.3. Adicionar o Arquivo de Credenciais do Google

1. Coloque o arquivo `credentials.json` (baixado no passo 1.4) na raiz da pasta do projeto.
2. Verifique se o caminho no `.env` está correto: `GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json`

### 3.4. Iniciar o Bot

1. Execute o bot:
   ```bash
   python bot.py
   ```

2. Se tudo estiver configurado corretamente, você verá mensagens como:
   ```
   INFO - Validando configurações...
   INFO - Inicializando clientes...
   INFO - Inicializando Google Sheets client...
   INFO - Inicializando Question Processor...
   INFO - ✅ Clientes inicializados com sucesso!
   INFO - 🚀 Iniciando bot na porta 5000...
   INFO - 📡 Callback URL: http://0.0.0.0:5000/callback
   ```

3. O servidor Flask estará rodando localmente na porta 5000.

---

## 4. Exposição do Servidor Local (ngrok)

Para que o SeaTalk possa enviar callbacks para o seu bot, você precisa expor o servidor local para a internet.

### 4.1. Instalar ngrok

1. Acesse [https://ngrok.com/](https://ngrok.com/) e crie uma conta gratuita.
2. Baixe e instale o `ngrok` seguindo as instruções do site.
3. Autentique o `ngrok` com seu token:
   ```bash
   ngrok authtoken SEU_TOKEN_AQUI
   ```

### 4.2. Expor a Porta 5000

1. Com o bot rodando (passo 3.4), abra um novo terminal.
2. Execute o comando:
   ```bash
   ngrok http 5000
   ```

3. O `ngrok` fornecerá uma URL pública, algo como:
   ```
   Forwarding   https://abc123.ngrok.io -> http://localhost:5000
   ```

4. **Copie a URL HTTPS** (ex: `https://abc123.ngrok.io`).

### 4.3. Finalizar Configuração do SeaTalk

1. Volte para a plataforma do SeaTalk Open Platform.
2. Vá para **"Event Subscriptions"** ou **"Event Callback"**.
3. Cole a URL do ngrok seguida de `/callback`:
   ```
   https://abc123.ngrok.io/callback
   ```
4. Cole o **Verification Token** que você criou no passo 2.5.
5. Clique em **"Save"** ou **"Verify"**.
6. O SeaTalk enviará uma requisição de verificação para o seu bot. Se tudo estiver correto, a verificação será bem-sucedida.

---

## 5. Teste e Validação

### 5.1. Adicionar o Bot no SeaTalk

1. Abra o aplicativo SeaTalk (desktop ou mobile).
2. Vá para **"Contacts"** ou **"Search"**.
3. Procure pelo nome do bot que você criou (ex: "Shopee Data Bot").
4. Clique no bot e inicie uma conversa.

### 5.2. Testar Comandos

Envie as seguintes mensagens para o bot:

1. `ajuda` - Deve retornar a lista de comandos disponíveis.
2. `colunas` - Deve listar as colunas da sua planilha.
3. `quantidade total` - Deve retornar a soma total da coluna de quantidade.
4. `top 5` - Deve retornar os 5 produtos com maior quantidade.

### 5.3. Teste Local (Sem SeaTalk)

Você também pode testar o bot localmente sem usar o SeaTalk:

```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"question": "quantidade total"}' \
http://127.0.0.1:5000/test
```

A resposta será retornada em formato JSON.

---

## 6. Solução de Problemas

### Problema: "Configurações obrigatórias faltando"

**Solução**: Verifique se o arquivo `.env` está preenchido corretamente com todas as credenciais.

### Problema: "Arquivo de credenciais não encontrado"

**Solução**: Certifique-se de que o arquivo `credentials.json` está na raiz do projeto e que o caminho no `.env` está correto.

### Problema: "Erro ao autenticar com Google Sheets"

**Solução**: 
- Verifique se as APIs do Google Sheets e Google Drive estão ativadas no GCP.
- Verifique se a planilha foi compartilhada com o email da conta de serviço.
- Verifique se o ID da planilha no `.env` está correto.

### Problema: "Bot não responde no SeaTalk"

**Solução**:
- Verifique se o servidor Flask está rodando.
- Verifique se o `ngrok` está ativo e a URL está correta no SeaTalk.
- Verifique os logs do bot para ver se as mensagens estão sendo recebidas.
- Verifique se o Verification Token no `.env` corresponde ao token configurado no SeaTalk.

### Problema: "Coluna não encontrada"

**Solução**: 
- Verifique se os nomes das colunas na planilha estão corretos.
- Use o comando `colunas` no bot para ver os nomes exatos das colunas.
- Ajuste as perguntas para usar os nomes corretos das colunas.

---

## Próximos Passos

Após configurar e testar o bot com sucesso, você pode:

- Personalizar as perguntas e respostas no arquivo `question_processor.py`.
- Adicionar novos tipos de análises no arquivo `data_analyzer.py`.
- Configurar um servidor permanente (ex: AWS, Heroku, DigitalOcean) para hospedar o bot em produção.
- Implementar autenticação e segurança adicionais.
- Adicionar logs e monitoramento mais avançados.

---

**Desenvolvido com ❤️ para facilitar a análise de dados da Shopee via SeaTalk.**
