"""
태스크와 투두 관련 데이터 모델
"""
from dataclasses import dataclass
from typing import List, Set, Optional
from .status import TaskState, TaskStatus

@dataclass
class TodoInfo:
    title: str
    number: int
    status: str
    weight: int
    assignees: Set[str]
    closed_at: Optional[str]

@dataclass
class TaskInfo:
    number: int
    title: str
    status: TaskStatus
    assignees: Set[str]
    priority: str
    expected_time: str
    todos: List[TodoInfo]
    category: str
    url: str 