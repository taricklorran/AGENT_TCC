# main.py
import logging
from fastapi import FastAPI
from routers.api_router import router as api_router
from config import settings
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# A aplicação FastAPI agora é mais simples
app = FastAPI(
    title=f"{settings.APP_NAME} - Health Check API",
    description="Serviço de Health Check para o AI Agent Worker.",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    """
    Verifica se o serviço está online. Útil para monitoramento em contêineres (Kubernetes, Docker).
    """
    return {"status": "healthy", "version": app.version}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )