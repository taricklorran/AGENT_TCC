# services/definitions/system_managers.py
from models.schemas import ManagerSchema, AgentSchema, ToolSchema, ParameterSchema

LIST_CAPABILITIES_TOOL = ToolSchema(
    tool_name="listCapabilities",
    description="Lista e descreve as principais capacidades e ferramentas disponíveis para ajudar o usuário.",
    parameters_mandatory=[],
    isApi=False,
    isLLM=False,
    isActive=True
)
META_MANAGER_DEFINITION = ManagerSchema(
    manager_id="SYS_META_MANAGER",
    description="Gerencia ferramentas sobre o próprio sistema, como listar capacidades.",
    isActive=True,
    is_system_tool=True,
    agents=[
        AgentSchema(
            agent_id="SYS_CAPABILITIES_AGENT",
            description="Agente que sabe descrever as funcionalidades do sistema.",
            isActive=True,
            tools=[LIST_CAPABILITIES_TOOL]
        )
    ]
)

# Usamos os Pydantic Schemas para garantir que a estrutura esteja sempre correta.
MEMORY_MANAGER_DEFINITION = ManagerSchema(
    manager_id="SYS_MEMORY_MANAGER",
    description="Especialista em acessar a memória de longo prazo do usuário para lembrar de conversas e informações passadas.",
    isActive=True,
    is_system_tool=True,
    agents=[
        AgentSchema(
            agent_id="SYS_RECALL_AGENT",
            description="Agente com a capacidade de buscar em resumos de conversas antigas.",
            isActive=True,
            tools=[
                ToolSchema(
                    tool_name="searchLongTermMemory",
                    description="Use para buscar informações ou contexto de conversas que aconteceram há mais de um dia. Ótima para perguntas como 'lembra quando falamos sobre X?' ou 'qual foi a decisão sobre Y?'.",
                    parameters_mandatory=[
                        ParameterSchema(
                            name="query",
                            type="string",
                            description="O tópico ou pergunta a ser buscado na memória.",
                            required=True
                        )
                    ],
                    isApi=False,
                    isLLM=False,
                    isActive=True
                )
            ]
        )
    ]
)