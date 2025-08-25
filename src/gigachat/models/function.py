from typing import Any, Dict, List, Optional

from gigachat.models.few_shot_example import FewShotExample
from gigachat.models.function_parameters import FunctionParameters
from gigachat.pydantic_v1 import BaseModel, root_validator


class Function(BaseModel):
    """Функция, которая может быть вызвана моделью"""

    name: str
    """Название функции"""
    description: Optional[str] = None
    """Описание функции"""
    parameters: Optional[FunctionParameters] = None
    """Список параметров функции"""
    few_shot_examples: Optional[List[FewShotExample]] = None
    return_parameters: Optional[Dict[Any, Any]] = None
    """Список возвращаемых параметров функции"""

    @root_validator(pre=True)
    def _fix_title_and_parameters(cls, values):
        """Pydantic adapter (title -> name), (parameters -> properties)"""
        if isinstance(values, dict):
            values = dict(values)

            if values.get("name") in (None, "") and values.get("title"):
                values["name"] = values.pop("title", None)

            if values.get("parameters") in (None, "", {}) and "properties" in values:
                values["parameters"] = {
                    "properties": values.pop("properties", {}),
                }

        return values
