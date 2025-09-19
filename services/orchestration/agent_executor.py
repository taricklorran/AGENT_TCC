# services/orchestration/agent_executor.py
from models.schemas import AgentSchema, ToolResult
from tools import get_tool_registry
import logging

class AgentExecutor:
    def __init__(self):
        self.tool_registry = get_tool_registry()
        self.logger = logging.getLogger(__name__)
    
    def execute_agent(self, agent: AgentSchema, tool_name: str, params: dict, context) -> ToolResult:
        try:

            # Validações iniciais
            if not agent or not tool_name:
                return ToolResult(
                    success=False,
                    output="Agente ou ferramenta inválidos"
                )
            
            self.logger.info(f"Agente '{agent.agent_id}' executando a ferramenta '{tool_name}'")
            
            # Encontrar definição da ferramenta
            tool_def = next((t for t in agent.tools if t.tool_name == tool_name), None)
            
            if tool_def.parameters_mandatory:
                mandatory_params = [
                    p.name for p in tool_def.parameters_mandatory if p.required
                ]
                missing_params = [p for p in mandatory_params if p not in params]

                if missing_params:
                    return ToolResult(
                        success=False,
                        next_step="REQUEST_USER_INPUT",
                        required_params=missing_params,
                        output=f"Parâmetros necessários para a ferramenta '{tool_name}': {', '.join(missing_params)}"
                    )
            
            implementation_key = ""
            # Supondo que o schema tenha o campo 'isLLM'
            if getattr(tool_def, 'isLLM', False): 
                implementation_key = "PromptExecutionTool"
            elif tool_def.isApi:
                implementation_key = "ExecutarAPI"
            else:
                implementation_key = tool_def.tool_name

            tool_impl = self.tool_registry.get_tool(implementation_key)

            #implementation = "ExecutarAPI" if tool_def.isApi else tool_def.tool_name
            #tool_impl = self.tool_registry.get_tool(implementation)

            if not tool_impl:
                return ToolResult(
                    success=False,
                    output=f"Implementação '{implementation_key}' não encontrada no registro"
                )
            if getattr(tool_def, 'isLLM', False) or tool_def.isApi:
                result = tool_impl.execute(params, context, tool_def)
            else:
                result = tool_impl.execute(params, context)

            return result           
            
        except Exception as e:
            failed_tool_name = getattr(tool_def, 'tool_name', 'desconhecida')
            self.logger.exception(f"Erro na execução da ferramenta {failed_tool_name}")

            return ToolResult(
                success=False,
                output=f"Erro na execução da ferramenta '{failed_tool_name}': {str(e)}"
            )
