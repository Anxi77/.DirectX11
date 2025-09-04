"""Field information model."""
from typing import List, Optional, Any, Dict
from dataclasses import dataclass

@dataclass
class FieldInfo:
    """Field information for project boards."""
    field_id: str
    name: str
    data_type: str
    options: Optional[List[Dict[str, Any]]] = None
