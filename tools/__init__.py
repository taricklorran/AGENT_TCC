from .registry import global_tool_registry

def get_tool_registry():
    """Retorna a instância global do registro de ferramentas."""
    return global_tool_registry