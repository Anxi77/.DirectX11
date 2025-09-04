"""Shared data models for the projects domain."""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any

class TaskStatus(Enum):
    """Task status enumeration."""
    TODO = "Todo"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"

class TaskPriority(Enum):
    """Task priority enumeration."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

@dataclass
class TaskItem:
    """Task item representation."""
    issue: Dict[str, Any]
    status: TaskStatus
    priority: TaskPriority
    category: Optional[str] = None
    assignee: Optional[str] = None
    board_item: Optional[Any] = None
