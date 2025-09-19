# routers/api_router.py
from fastapi import APIRouter, HTTPException, status
from models.schemas import UserRequest
from worker import process_ai_request
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ask", status_code=status.HTTP_202_ACCEPTED)
def ask_question(request: UserRequest):
    """
    Recebe uma pergunta, a enfileira para processamento assíncrono
    e retorna imediatamente.
    """
    try:
        # 3. Garante que a tarefa e a sessão tenham um ID único
        task_id = request.task_id or str(uuid.uuid4())
        session_id = request.session_id or str(uuid.uuid4())

        # 4. Monte o payload que o seu worker espera receber
        job_payload = {
            "task_id": task_id,
            "user_id": request.user_id,
            "session_id": session_id,
            "user_input": request.question,
            "callback_details": {
                "webhook_url": request.webhook_url,
                "addressing_info": request.addressing_info
            }
        }

        # 5. Envie a tarefa para a fila do Dramatiq.
        #    Esta chamada é instantânea, apenas coloca a mensagem no Redis.
        process_ai_request.send(job_payload)

        logger.info(f"Tarefa {task_id} para o usuário {request.user_id} foi enfileirada com sucesso.")

        # 6. Responda IMEDIATAMENTE ao usuário com os IDs para rastreamento.
        return {
            "message": "Sua requisição foi aceita e está sendo processada em segundo plano.",
            "task_id": task_id,
            "session_id": session_id
        }

    except Exception as e:
        logger.exception("Erro CRÍTICO ao enfileirar a tarefa na rota /ask")
        raise HTTPException(
            status_code=500,
            detail=f"Não foi possível enfileirar a tarefa para processamento: {e}"
        )