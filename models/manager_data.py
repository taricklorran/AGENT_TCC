from typing import List
from models.schemas import ManagerSchema

from services.definitions.definition_loader import definition_loader

def get_managers(user_id: str) -> List[ManagerSchema]:
    """
    Busca os managers permitidos para um usuário a partir do cache de definições.
    Esta operação é extremamente rápida, pois não acessa mais o banco de dados.
    """
    return definition_loader.get_managers_for_user(user_id)