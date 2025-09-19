# tools/plugins/system_tools.py
from tools.base_tool import BaseTool
from models.schemas import ToolResult, ExecutionContext

class ListCapabilitiesTool(BaseTool):
    """
    Uma ferramenta de sistema que inspeciona o contexto da execução
    para listar todas as ferramentas públicas (não de sistema) disponíveis.
    """
    @property
    def name(self) -> str:
        return "listCapabilities"

    @property
    def description(self) -> str:
        return "Lista e descreve as principais capacidades e ferramentas disponíveis para ajudar o usuário."

    @property
    def mandatory_params(self) -> list[str]:
        return []

    def execute(self, params: dict, context: ExecutionContext) -> ToolResult:
        """
        Filtra os managers no contexto e cria uma descrição formatada.
        """
        public_managers = [
            manager for manager in context.available_managers if not manager.is_system_tool
        ]

        if not public_managers:
            return ToolResult(success=True, output="No momento, não tenho ferramentas específicas disponíveis.")

        # Formata a saída de forma amigável para o usuário
        output_lines = ["Claro! Eu posso te ajudar com as seguintes capacidades:"]
        for manager in public_managers:
            output_lines.append(f"\n- **{manager.description}**:")
            for agent in manager.agents:
                for tool in agent.tools:
                    output_lines.append(f"  - {tool.description}")

        final_output = "\n".join(output_lines)
        return ToolResult(success=True, output=final_output)