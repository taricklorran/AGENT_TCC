from pydantic import BaseModel, Field  
from typing import List, Dict, Any, Optional

class ParameterSchema(BaseModel):
    name: str
    type: str
    description: str
    required: bool

class ApiAuthConfig(BaseModel):
    type: str
    token: Optional[str] = None

class ApiConfigSchema(BaseModel):
    method: str
    base_url: str
    auth: ApiAuthConfig
    headers: Dict[str, str]
    body_template: Optional[Any] = None

class ToolSchema(BaseModel):
    tool_name: str
    description: str
    parameters_mandatory: List[ParameterSchema]
    isApi: bool
    api_config: Optional[ApiConfigSchema] = None
    isLLM: bool
    prompt_template: Optional[str] = None
    isActive: bool

class AgentSchema(BaseModel):
    agent_id: str
    description: str
    isActive: bool
    tools: List[ToolSchema]
    response_guideline: Optional[str] = Field(None, description="Instrução sobre como formatar a contribuição deste agente na resposta final ao usuário.")

class ManagerSchema(BaseModel):
    manager_id: str
    description: str
    isActive: bool
    agents: List[AgentSchema]
    is_system_tool: bool = Field(default=False, description="Indica se o manager é uma ferramenta interna do sistema e não deve ser exposto ao usuário.")

class UserRequest(BaseModel):
    user_id: str
    question: str
    session_id: Optional[str] = None
    task_id: Optional[str] = Field(None, description="ID único para rastrear esta tarefa específica.")
    webhook_url: Optional[str] = Field(None, description="URL de callback para notificar o resultado final.")
    addressing_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Dados adicionais a serem retornados no callback.")

class ToolResult(BaseModel):
    success: bool
    output: Any
    next_step: Optional[str] = None  # CONTINUE, REPEAT, REQUEST_USER_INPUT
    required_params: Optional[List[str]] = None

class ExecutionContext(BaseModel):
    session_id: str
    user_id: str
    user_question: str
    previous_results: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    react_history: List[str] = Field(default_factory=list)  # Única definição
    final_output: Optional[str] = None
    pending_actions: List[dict] = Field(default_factory=list)
    execution_id: Optional[str] = None
    user_data: Dict[str, Any] = Field(default_factory=dict)  # Corrigido para Field
    plan_state: Optional[dict] = None
    available_managers: List[ManagerSchema] = Field(default_factory=list)
    available_agents: List[AgentSchema] = Field(default_factory=list)