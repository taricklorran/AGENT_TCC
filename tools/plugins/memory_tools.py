# tools/plugins/memory_tools.py
import os
from datetime import datetime
import google.generativeai as genai
from qdrant_client import QdrantClient, models
from config import settings
from tools.base_tool import BaseTool
from models.schemas import ToolResult, ExecutionContext

class SearchLongTermMemoryTool(BaseTool):
    """
    Ferramenta para buscar na memória de longo prazo do usuário por conversas passadas
    relevantes para a consulta atual, usando busca vetorial no Qdrant.
    """
    
    # Atributos de classe para armazenar a conexão, garantindo reuso.
    _qdrant_client: QdrantClient = None
    _collection_name = "long_term_memory"
    _embedding_model = "models/embedding-001"

    def _get_qdrant_client(self) -> QdrantClient:
        """
        Garante que a conexão com o Qdrant seja estabelecida sob demanda
        e retorna o cliente. Reutiliza a conexão existente se já foi criada.
        """
        if SearchLongTermMemoryTool._qdrant_client is None:
            try:
                # Conecta apenas se ainda não houver uma conexão ativa
                SearchLongTermMemoryTool._qdrant_client = QdrantClient(
                    host=settings.QDRANT_URL,
                    port=settings.QDRANT_PORT
                )
                print(f"Processo PID:{os.getpid()}: Conexão com o Qdrant estabelecida.")
            except Exception as e:
                print(f"ERRO: Falha ao conectar ao Qdrant para a ferramenta de memória: {e}")
                return None
        return SearchLongTermMemoryTool._qdrant_client

    @property
    def name(self) -> str:
        return "searchLongTermMemory"
    
    @property
    def description(self) -> str:
        return "Use para buscar informações ou contexto de conversas que aconteceram há mais de um dia. Ótima para perguntas como 'lembra quando falamos sobre X?' ou 'qual foi a decisão sobre Y?'."
    
    @property
    def mandatory_params(self) -> list[str]:
        return ["query"]
        
    def _embed_text(self, text: str) -> list:
        """Helper privado para criar o embedding vetorial para um texto."""
        try:
            result = genai.embed_content(model=self._embedding_model, content=text)
            return result['embedding']
        except Exception as e:
            print(f"Erro ao criar embedding: {e}")
            return []

    def execute(self, params: dict, context: ExecutionContext) -> ToolResult:
        """
        Executa a busca vetorial no Qdrant e retorna o resultado.
        """
        # 1. Garante que o cliente do Qdrant existe
        qdrant_client = self._get_qdrant_client()
        if not qdrant_client:
            return ToolResult(success=False, output="Ferramenta de memória não disponível devido a erro de conexão.")

        # 2. Obter 'query' dos parâmetros e 'user_id' do contexto
        query = params.get("query")
        if not query:
            return ToolResult(success=False, output="Parâmetro 'query' não fornecido para a busca na memória.")
            
        user_id = context.user_data.get("user_id")
        if not user_id:
            return ToolResult(success=False, output="Não foi possível identificar o usuário para a busca na memória.")
            
        # 3. Vetorizar a query do usuário
        query_embedding = self._embed_text(query)
        if not query_embedding:
            return ToolResult(success=False, output="Não foi possível processar a busca na memória de longo prazo.")

        # 4. Executar a busca vetorial no Qdrant
        try:
            search_results = qdrant_client.search(
                collection_name=self._collection_name,
                query_vector=query_embedding,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id),
                        )
                    ]
                ),
                limit=3
            )

            if not search_results:
                return ToolResult(success=True, output="Nenhuma memória relevante encontrada em conversas passadas.")

            # 5. Formatar a saída para ser útil para a LLM
            formatted_results = "\n\n".join([
                f"Memória de {datetime.fromisoformat(hit.payload['conversation_end']).strftime('%d/%m/%Y')}:\n'{hit.payload['summary']}' (similaridade: {hit.score:.2f})"
                for hit in search_results
            ])
            
            final_output = f"Encontrei as seguintes memórias relevantes de conversas passadas:\n{formatted_results}"
            return ToolResult(success=True, output=final_output)

        except Exception as e:
            return ToolResult(success=False, output=f"Erro ao executar a busca na memória (Qdrant): {str(e)}")