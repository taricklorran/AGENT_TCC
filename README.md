# IA Agent Orchestrator

Este projeto é um orquestrador de agentes de IA projetado para processar tarefas de forma assíncrona. Ele usa uma API FastAPI para receber trabalhos, um broker Redis com Dramatiq para enfileirar e processar tarefas e MongoDB para armazenamento de dados.

## Começando

Estas instruções fornecerão uma cópia do projeto em funcionamento em sua máquina local para fins de desenvolvimento e teste.

### Pré-requisitos

O que você precisa para executar o projeto:

*   Python 3.9+
*   Docker e Docker Compose (opcional, para execução em contêiner)
*   Redis
*   MongoDB (instalado localmente)

### Instalação

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/taricklorran/AGENT_TCC.git
    cd seu-repositorio
    ```

2.  **Crie e ative um ambiente virtual:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows, use `venv\Scripts\activate`
    ```

3.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Crie um arquivo `.env`** na raiz do projeto e adicione as seguintes variáveis de ambiente. Para execução com Docker, altere `localhost` para `host.docker.internal` no `MONGO_URI`.

    ```env
    GEMINI_API_KEY=sua_chave_de_api_gemini
    GEMINI_MODEL=gemini-1.5-flash-preview-0514
    MONGO_URI=mongodb://localhost:27017
    MONGO_DB=ai_agents
    RAG_BASE_URL=http://localhost:3333
    RAG_API_TOKEN=seu_token_rag
    QDRANT_URL=http://localhost
    QDRANT_PORT=6333
    ```

### Uso

Para executar o projeto, você precisará iniciar o servidor da API e o worker do Dramatiq.

1.  **Inicie o servidor da API:**

    ```bash
    python main.py
    ```

    O servidor estará disponível em `http://localhost:8000`.

2.  **Inicie o worker do Dramatiq:**

    Em um novo terminal, execute o seguinte comando:

    ```bash
    dramatiq worker --threads 8
    ```
    ou use o script de lote:
    ```bash
    run_worker.bat
    ```