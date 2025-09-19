# tools/registry.py
from typing import Dict, Type
from .base_tool import BaseTool
import pkgutil
import importlib
import inspect
import logging

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self.logger = logging.getLogger(__name__)
        self._discover_and_register_tools()

    def _discover_and_register_tools(self):
        """
        Escaneia o pacote 'tools.plugins', encontra classes que herdam de BaseTool
        e as registra automaticamente.
        """
        import tools.plugins as plugins_package
        
        self.logger.info("Iniciando descoberta de ferramentas...")
        
        # Itera sobre todos os módulos dentro do pacote 'tools.plugins'
        for _, module_name, _ in pkgutil.iter_modules(plugins_package.__path__, plugins_package.__name__ + "."):
            try:
                module = importlib.import_module(module_name)
                
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Verifica se a classe é uma subclasse de BaseTool e não a própria BaseTool
                    if issubclass(obj, BaseTool) and obj is not BaseTool:
                        # Instancia a classe e a registra usando a propriedade 'name'
                        instance = obj({})
                        if instance.name in self._tools:
                            self.logger.warning(f"Ferramenta '{instance.name}' já registrada. Sobrescrevendo.")
                        
                        self._tools[instance.name] = instance
                        self.logger.info(f"✅ Ferramenta '{instance.name}' registrada com sucesso.")
            
            except Exception as e:
                self.logger.error(f"Falha ao carregar ou registrar ferramentas do módulo '{module_name}': {e}")


    def get_tool(self, tool_name: str) -> BaseTool:
        """Obtém uma ferramenta pelo nome"""
        tool = self._tools.get(tool_name)
        if not tool:
            raise ValueError(f"Ferramenta '{tool_name}' não registrada")
        return tool
    
    def list_tools(self) -> Dict[str, BaseTool]:
        """Lista todas as ferramentas registradas"""
        return self._tools.copy()

global_tool_registry = ToolRegistry()