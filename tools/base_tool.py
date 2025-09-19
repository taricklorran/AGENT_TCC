# tools/base_tool.py
from abc import ABC, abstractmethod
from models.schemas import ToolResult, ExecutionContext
from pydantic import BaseModel

class BaseToolConfig(BaseModel):
    pass

class BaseTool(ABC):
    context_updated = False
    
    def __init__(self, config: dict):
        self.config = BaseToolConfig(**config)
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def mandatory_params(self) -> list:
        pass

    @abstractmethod
    def execute(self, params: dict, context: ExecutionContext) -> ToolResult:
        pass