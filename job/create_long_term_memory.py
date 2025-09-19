# job/create_long_term_memory.py
import os
import uuid
import google.generativeai as genai
from pymongo import MongoClient
from qdrant_client import QdrantClient, models
from datetime import datetime, timedelta, timezone
from config import settings
from dotenv import load_dotenv

# --- Configuração ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Configs do MongoDB (para a Memória de Curto Prazo)
MONGO_URI = settings.MONGO_URI
MONGO_DB = settings.MONGO_DB
CONVERSATION_HISTORY_COLLECTION = "conversation_history"

# Configs do Qdrant (para a Memória de Longo Prazo)
QDRANT_HOST = settings.QDRANT_URL
QDRANT_PORT = settings.QDRANT_PORT
QDRANT_COLLECTION_NAME = "long_term_memory"

# Configs dos Modelos de IA
EMBEDDING_MODEL = "models/embedding-001"
GENERATIVE_MODEL = "gemini-1.5-flash"
VECTOR_SIZE = 768 # Tamanho do vetor para o modelo embedding-001 do Google

# --- Funções Auxiliares (sem alterações) ---

def summarize_conversation(conversation_text: str) -> str:
    """Usa a LLM para criar um resumo conciso da conversa."""
    model = genai.GenerativeModel(GENERATIVE_MODEL)
    prompt = f"""
    Resuma a seguinte conversa entre um usuário e um assistente de IA em um ou dois parágrafos.
    Foque nos principais problemas resolvidos, informações chave trocadas e no resultado final.
    Não inclua saudações ou despedidas, vá direto ao ponto.

    CONVERSA:
    {conversation_text}

    RESUMO CONCISO:
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Erro ao sumarizar: {e}")
        return ""

def embed_text(text: str) -> list:
    """Cria o embedding vetorial para um texto."""
    try:
        result = genai.embed_content(model=EMBEDDING_MODEL, content=text)
        return result['embedding']
    except Exception as e:
        print(f"Erro ao criar embedding: {e}")
        return []

# --- Lógica Principal Modificada ---

def main():
    print("Iniciando rotina de criação de memória de longo prazo...")
    
    # Conexão com a Memória de Curto Prazo (MongoDB)
    mongo_client = MongoClient(MONGO_URI)
    stm_collection = mongo_client[MONGO_DB][CONVERSATION_HISTORY_COLLECTION]
    
    # Conexão com a Memória de Longo Prazo (Qdrant)
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Garante que a coleção no Qdrant exista
    try:
        qdrant_client.recreate_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
        )
        print(f"Coleção '{QDRANT_COLLECTION_NAME}' criada/recriada no Qdrant.")
    except Exception as e:
        print(f"Coleção '{QDRANT_COLLECTION_NAME}' já existe ou houve um erro: {e}")

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=0)
    pipeline = [
        {"$sort": {"timestamp": 1}},
        {"$group": {
            "_id": "$session_id",
            "last_message_time": {"$last": "$timestamp"},
            "messages": {"$push": "$$ROOT"},
            "user_id": {"$first": "$user_id"}
        }},
        {"$match": {"last_message_time": {"$lt": cutoff_date}}}
    ]
    sessions_to_process = list(stm_collection.aggregate(pipeline))
    print(f"Encontradas {len(sessions_to_process)} sessões para processar.")

    points_to_upsert = []
    processed_session_ids = []

    for session in sessions_to_process:
        session_id = session["_id"]
        user_id = session["user_id"]
        messages = session["messages"]
        
        print(f"Processando sessão: {session_id}")

        conversation_text = "\n".join([f"{msg['role']}: {msg['message']}" for msg in messages])

        summary = summarize_conversation(conversation_text)
        if not summary:
            print(f"  - Falha ao sumarizar. Pulando sessão {session_id}.")
            continue
        print(f"  - Resumo gerado: {summary[:80]}...")

        embedding = embed_text(summary)
        if not embedding:
            print(f"  - Falha ao vetorizar. Pulando sessão {session_id}.")
            continue
        print(f"  - Vetor gerado com sucesso.")

        # 5. Preparar os dados para salvar no Qdrant
        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "summary": summary,
            "conversation_start": messages[0]["timestamp"].isoformat(),
            "conversation_end": messages[-1]["timestamp"].isoformat(),
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Cada ponto no Qdrant tem um ID, um vetor e um payload.
        point = models.PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload=payload
        )
        points_to_upsert.append(point)
        processed_session_ids.append(session_id)

    # 6. Salvar todos os pontos na Memória de Longo Prazo (Qdrant) em uma única chamada
    if points_to_upsert:
        qdrant_client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=points_to_upsert,
            wait=True
        )
        print(f"  - {len(points_to_upsert)} resumos salvos na memória de longo prazo (Qdrant).")

        # 7. Limpar a memória de curto prazo (MongoDB)
        # Encontra todos os _id's das mensagens das sessões processadas
        ids_to_delete_cursor = stm_collection.find(
            {"session_id": {"$in": processed_session_ids}}, 
            {"_id": 1}
        )
        ids_to_delete = [doc["_id"] for doc in ids_to_delete_cursor]
        
        if ids_to_delete:
            stm_collection.delete_many({"_id": {"$in": ids_to_delete}})
            print(f"  - {len(ids_to_delete)} mensagens limpas da memória de curto prazo (MongoDB).")

    print("Rotina finalizada.")

if __name__ == "__main__":
    main()

# iniciar o job python -m job.create_long_term_memory