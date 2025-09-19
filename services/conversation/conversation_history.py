import json
import os
from datetime import datetime, timezone
from collections import defaultdict

# 1. Importar as bibliotecas do MongoDB
from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection

from config import settings

class ConversationHistory:
    _instance = None
    
    # 2. Atributos para a conexão com o banco de dados
    _client: MongoClient = None
    _db = None
    _collection: Collection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConversationHistory, cls).__new__(cls)
            
            # 3. Conectar ao MongoDB na primeira inicialização
            try:
                cls._client = MongoClient(settings.MONGO_URI)
                cls._db = cls._client[settings.MONGO_DB]
                cls._collection = cls._db["conversation_history"]
                # 4. Criar índices para otimizar buscas por sessão e data
                cls._collection.create_index("session_id")
                cls._collection.create_index([("session_id", 1), ("timestamp", 1)])
                print("[CONVERSATION_HISTORY] Conectado ao MongoDB com sucesso.")
            except Exception as e:
                print(f"[CONVERSATION_HISTORY] ERRO CRÍTICO: Não foi possível conectar ao MongoDB. {e}")
                cls._collection = None

            # O cache em memória pode ser mantido para otimizar leituras repetidas na mesma sessão
            cls._instance._session_registry_cache = defaultdict(list)
        return cls._instance

    def log_message(
        self,
        session_id: str,
        execution_id: str,
        role: str,
        user_id: str,
        message: str
    ):
        """Registra uma nova mensagem diretamente no MongoDB."""
        if self._collection is None:
            print("[CONVERSATION_HISTORY] ERRO: Não é possível logar mensagem. Sem conexão com o MongoDB.")
            return None
            
        entry = {
            "session_id": session_id,
            "execution_id": execution_id,
            "role": role,
            "user_id": user_id,
            "message": message,
            "timestamp": datetime.now(timezone.utc)
        }
        
        try:
            # 5. Insere a nova mensagem como um documento. Esta operação é atômica.
            self._collection.insert_one(entry)
            
            # Limpa o cache para esta sessão para forçar a releitura do DB na próxima vez
            if session_id in self._session_registry_cache:
                del self._session_registry_cache[session_id]

        except Exception as e:
            if settings.DEBUG:
                print(f"[CONVERSATION_HISTORY] Erro ao salvar mensagem no MongoDB: {str(e)}")
        
        return entry

    def get_conversation_history(self, session_id: str) -> list:
        """Recupera o histórico completo de uma sessão diretamente do MongoDB."""
        # Primeiro, verifica o cache para evitar chamadas repetidas ao DB
        if session_id in self._session_registry_cache:
            return self._session_registry_cache[session_id]

        if self._collection is None:
            return []

        try:
            # 6. Busca todos os documentos da sessão, ordenados por tempo
            history_cursor = self._collection.find(
                {"session_id": session_id}
            ).sort("timestamp", 1) # 1 para ordem ascendente
            
            history = list(history_cursor)
            
            # Atualiza o cache
            self._session_registry_cache[session_id] = history
            return history
        except Exception as e:
            if settings.DEBUG:
                print(f"[CONVERSATION_HISTORY] Erro ao buscar histórico no MongoDB: {str(e)}")
        
        return []

    def get_last_messages(self, session_id: str, num_messages: int = 5) -> list:
        """Recupera as últimas N mensagens de forma otimizada do MongoDB."""
        if self._collection is None:
            return []
            
        try:
            projection = {
                "role": 1,
                "user_id": 1,
                "message": 1,
                "timestamp": 1
            }

            history_cursor = self._collection.find(
                {"session_id": session_id},
                projection  # Aplicando a projeção
            ).sort("timestamp", DESCENDING).limit(num_messages)
            
            # O resultado vem do mais novo para o mais antigo, então revertemos para a ordem cronológica
            return list(reversed(list(history_cursor)))
        except Exception as e:
            if settings.DEBUG:
                print(f"[CONVERSATION_HISTORY] Erro ao buscar últimas mensagens no MongoDB: {str(e)}")
        
        return []

    def clear_session_history(self, session_id: str):
        """Remove todo o histórico de uma sessão do MongoDB."""
        # Limpa o cache
        if session_id in self._session_registry_cache:
            del self._session_registry_cache[session_id]

        if self._collection is None:
            return

        try:
            # 8. Deleta todos os documentos que correspondem ao session_id
            result = self._collection.delete_many({"session_id": session_id})
            if settings.DEBUG:
                print(f"[CONVERSATION_HISTORY] Histórico para a sessão {session_id} limpo. {result.deleted_count} mensagens removidas.")
        except Exception as e:
            if settings.DEBUG:
                print(f"[CONVERSATION_HISTORY] Erro ao limpar histórico no MongoDB: {str(e)}")

# Instância global do logger de histórico
conversation_history = ConversationHistory()