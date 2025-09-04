"""Board item model."""
from typing import Optional, Any, Dict
from dataclasses import dataclass

@dataclass
class BoardItem:
    """Board item with content and field values."""
    item_id: str
    content_id: Optional[str] = None
    content_type: Optional[str] = None
    content_number: Optional[int] = None
    content_title: Optional[str] = None
    field_values: Optional[Dict[str, Any]] = None
