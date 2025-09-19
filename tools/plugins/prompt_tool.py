# tools/plugins/prompt_tools.py
from tools.base_tool import BaseTool
from models.schemas import ToolResult, ExecutionContext, ToolSchema
from services.llm.gemini_adapter import GeminiAdapter

class PromptExecutionTool(BaseTool):
    """
    Uma ferramenta genérica e stateless que executa qualquer prompt definido dinamicamente
    passado para o seu método 'execute'.
    """

    @property
    def name(self):
        # O nome é genérico, pois a ferramenta real é definida no ToolSchema
        return "PromptExecutionTool"

    @property
    def description(self):
        # A descrição também é genérica
        return "Um motor de execução para ferramentas baseadas em prompts de LLM."
    
    @property
    def mandatory_params(self):
        return []
    
    def execute(self, params: dict, context: ExecutionContext, tool_def: ToolSchema) -> ToolResult:
        prompt_template = tool_def.prompt_template
        if not prompt_template:
            return ToolResult(success=False, output=f"Ferramenta '{tool_def.tool_name}' não possui um template de prompt configurado.")

        try:
            # Preenche o template com os parâmetros recebidos
            formatted_prompt = prompt_template.format(**params)
        except KeyError as e:
            return ToolResult(success=False, output=f"Erro ao formatar o prompt para '{tool_def.tool_name}'. Parâmetro ausente: {e}")

        try:
            gemini = GeminiAdapter()
            # Executa a LLM com o prompt formatado
            result = gemini.generate(formatted_prompt)
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, output=f"Ocorreu um erro ao executar o prompt na LLM: {e}")