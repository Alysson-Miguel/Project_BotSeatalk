# Bot SeaTalk para Análise de Indicadores de Performance

Este projeto implementa um bot inteligente para SeaTalk que se integra com o Google Sheets para fornecer análises de **indicadores de performance e KPIs** da Shopee. O bot é capaz de responder a perguntas sobre indicadores, explicar suas lógicas, identificar problemas e fornecer insights acionáveis diretamente no chat do SeaTalk.

## 🚀 Funcionalidades Principais

- **🤖 Integração com IA (Groq)**: Utiliza inteligência artificial para responder perguntas complexas sobre indicadores
- **📊 Análise de Indicadores**: Monitora performance de KPIs como GMV, conversão, CTR, etc.
- **📋 Explicação de Lógicas**: Explica como cada indicador é calculado e sua importância
- **🚨 Detecção de Problemas**: Identifica automaticamente indicadores fora do target
- **📈 Relatórios Inteligentes**: Gera resumos e análises dos maiores ofensores
- **💬 Interface Natural**: Responde em linguagem natural através do SeaTalk
- **📱 Suporte Multi-Aba**: Trabalha com múltiplas planilhas (indicadores principais e leftover)
- **🔄 Atualização em Tempo Real**: Conecta-se ao Google Sheets para dados sempre atualizados

## 📁 Estrutura do Projeto

```
/shopee_seatalk_bot
|-- app.py                    # 🚀 Aplicação principal Flask (servidor do bot)
|-- config.py                 # ⚙️ Módulo de configuração e variáveis de ambiente
|-- AI/
|   |-- groq_client.py        # 🤖 Cliente para integração com IA Groq
|-- Functions/
|   |-- question_processor.py # 🧠 Processador inteligente de perguntas sobre indicadores
|   |-- seatalk_client.py     # 💬 Cliente para comunicação com API do SeaTalk
|   |-- sheets_client.py      # 📊 Cliente para leitura do Google Sheets
|   |-- data_analyzer.py      # 📈 Analisador de dados e indicadores
|-- requirements.txt          # 📦 Dependências do Python
|-- credentials.json          # 🔐 Credenciais do Google Sheets (não versionado)
|-- .env                      # 🔧 Variáveis de ambiente (não versionado)
|-- README.md                 # 📖 Este arquivo
|-- test_corrections.py       # 🧪 Script de testes das correções
```

## Guia de Instalação e Configuração

Siga os passos abaixo para configurar e executar o bot em seu ambiente.

### 1. 📋 Pré-requisitos

- **Python 3.8+** - Linguagem de programação
- **Conta SeaTalk** - Com permissões de administrador para criar apps
- **Google Cloud Platform** - Para configurar API do Google Sheets  
- **Planilha Google Sheets** - Com dados dos indicadores organizados
- **Conta Groq** - Para funcionalidades de IA (opcional mas recomendado)

### 2. Instalação das Dependências

Clone o repositório e instale as bibliotecas Python necessárias:

```bash
git clone <URL_DO_REPOSITORIO> # (simulado)
cd shopee_seatalk_bot
pip install -r requirements.txt
pip install --upgrade -r requirements.txt
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

### 5. 🔧 Configuração do Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```ini
# 💬 SeaTalk Configuration
SEATALK_APP_ID=seu_app_id_aqui
SEATALK_APP_SECRET=seu_app_secret_aqui
SEATALK_CALLBACK_TOKEN=seu_token_de_verificacao_aqui

# 📊 Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEET_ID=seu_id_da_planilha_aqui
GOOGLE_SHEET_RANGE=Sheet1!A1:Z1000
GOOGLE_SHEET_RANGE_2=Leftover!A1:Z1000

# 🤖 IA Configuration (Opcional)
GROQ_API_KEY=sua_chave_groq_aqui

# 🌐 Server Configuration
HOST=0.0.0.0
PORT=5000
DEBUG=True
```

> **💡 Dica**: Para obter uma chave Groq gratuita, acesse [console.groq.com](https://console.groq.com)

### 6. 🚀 Execução do Bot

Com tudo configurado, inicie o servidor:

```bash
python app.py
```

Se tudo estiver correto, você verá:
```
🚀 Iniciando Bot SeaTalk...
✅ Groq inicializado!
✅ Sheets e Processor PRONTOS!
🌐 Servidor rodando em 0.0.0.0:5000
```

Use o `ngrok` para expor a porta local:
```bash
ngrok http 5000
```

Finalize a configuração do callback no SeaTalk com a URL do ngrok.

## 💬 Como Usar o Bot

Após adicionar o bot a um chat no SeaTalk, você pode interagir com ele enviando mensagens. Digite `ajuda` para ver a lista completa de comandos disponíveis.

### 📋 Comandos Principais

**🎯 Consultas de Indicadores:**
- `!Indicadores` - Mostra status atual dos indicadores de performance
- `!Fora do target` - Lista indicadores que estão fora do target
- `!Ofensores` - Mostra os piores indicadores (maiores ofensores)

**📘 Explicações e Lógicas:**
- `Explicar [Nome do Indicador]` - Explica como um indicador específico é calculado
- `Quais indicadores existem?` - Lista todos os indicadores disponíveis
- `Explica todos` - Mostra explicação completa de todos os indicadores

**📊 Dados Secundários:**
- `!Leftover` - Mostra dados da aba secundária (sobras/leftover)
- `!Sobras` - Alias para leftover

**🔧 Utilitários:**
- `status` - Verifica status de conexões e dados
- `colunas` - Lista colunas disponíveis nas planilhas
- `recarregar` - Atualiza dados do Google Sheets
- `ajuda` - Mostra lista completa de comandos

### 💡 Exemplos de Uso

```
Usuário: !Indicadores
Bot: 📋 Indicadores Performance SITE
     📌 Resumo do dia: 24/01/2026
     [Tabela com status dos indicadores]


Usuário: !Fora do target
Bot: 🚨 Indicadores Fora do Target:
     [Lista dos indicadores problemáticos]
```

## 🧪 Como Testar

### Teste Local (Sem SeaTalk)
Você pode testar o processamento de perguntas localmente:

```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"question": "!Indicadores"}' \
http://127.0.0.1:5000/test
```

### Teste de Correções
Execute o script de testes para verificar se tudo está funcionando:

```bash
python test_corrections.py
```

### Comandos de Inicialização
```bash
# Terminal 1: Inicia o ngrok
ngrok http 5000

# Terminal 2: Inicia o bot
python app.py
```

## 🔧 Estrutura das Planilhas

### Aba Principal (Indicadores)
Deve conter colunas como:
- Nome do Indicador
- Valor Atual  
- Target/Meta
- Status (Verde/Amarelo/Vermelho)
- Período

### Aba "Logica indicadores" 
Para explicações automáticas:
- Coluna A: Nome do Indicador
- Coluna B: Explicação/Lógica de cálculo

### Aba Secundária (Leftover)
Dados complementares ou sobras do dia anterior.

## 🆕 Melhorias Implementadas

### ✅ Correções de Bugs
- **Mensagens duplicadas**: Removido callback conflitante
- **Logs duplicados**: Configuração otimizada de logging  
- **IA respondendo múltiplas vezes**: Lógica de fallback refinada
- **Métodos obsoletos**: Removidos métodos focados em produtos

### 🚀 Novas Funcionalidades  
- **Foco em indicadores**: Sistema adaptado para KPIs ao invés de produtos
- **Explicações automáticas**: Integração com aba "Logica indicadores"
- **Detecção de problemas**: Identifica indicadores fora do target
- **IA contextual**: Prompt otimizado para análise de indicadores
- **Comandos intuitivos**: Interface mais amigável e clara

### 🎯 Otimizações
- **Performance**: Delays reduzidos no envio de mensagens
- **Confiabilidade**: Melhor tratamento de erros
- **Usabilidade**: Comandos mais intuitivos e help melhorado

## 🚨 Troubleshooting

### Problema: Bot responde 2 vezes
✅ **Resolvido**: Callback duplicado foi removido do `seatalk_client.py`

### Problema: Logs duplicados  
✅ **Resolvido**: Configuração de logging otimizada no `app.py`

### Problema: IA responde mesmo quando não deveria
✅ **Resolvido**: Lógica de fallback refinada

### Erro: "Não consegui carregar dados"
- Verifique se `GOOGLE_SHEET_ID` está correto
- Confirme se `credentials.json` existe e tem permissões
- Teste a conexão com `status`

### Erro: "IA não disponível"
- Verifique se `GROQ_API_KEY` está configurada
- Confirme se a chave é válida no console.groq.com

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+** - Linguagem principal
- **Flask** - Framework web para webhooks
- **Pandas** - Análise e manipulação de dados
- **Google Sheets API** - Integração com planilhas
- **SeaTalk API** - Comunicação com chat corporativo
- **Groq API** - Inteligência artificial (Llama 3.3 70B)
- **Requests** - Cliente HTTP para APIs

## 📈 Roadmap Futuro

- [ ] Dashboard web para visualização de indicadores
- [ ] Alertas proativos para indicadores críticos  
- [ ] Integração com mais fontes de dados
- [ ] Análises preditivas com IA
- [ ] Relatórios automatizados por email
- [ ] Suporte a múltiplas linguagens

## 👥 Contribuição

Este projeto foi desenvolvido para automatizar o monitoramento de indicadores de performance da Shopee, proporcionando insights rápidos e acionáveis através de uma interface conversacional intuitiva.

---

**Desenvolvido com ❤️ para otimizar o acompanhamento de KPIs da Shopee**