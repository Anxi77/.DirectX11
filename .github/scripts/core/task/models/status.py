"""
태스크 상태 관련 모델
"""
from enum import Enum
from dataclasses import dataclass

class TaskState(Enum):
    """태스크 상태"""
    WAITING = ("⬜ 대기중", "⬜")
    IN_PROGRESS = ("🟡 진행중", "🟡")
    COMPLETED = ("✅ 완료", "✅")
    BLOCKED = ("❌ 차단", "❌")
    
    def __init__(self, label: str, icon: str):
        self.label = label
        self.icon = icon
    
    @property
    def priority(self) -> int:
        return {
            TaskState.WAITING: 0,
            TaskState.IN_PROGRESS: 1,
            TaskState.COMPLETED: 2,
            TaskState.BLOCKED: 3
        }[self]

class ReportSection(Enum):
    """리포트 섹션"""
    SUMMARY = "요약"
    COMPLETED = "완료된 태스크"
    IN_PROGRESS = "진행중인 태스크"
    WAITING = "대기중인 태스크"
    BLOCKED = "차단된 태스크"

@dataclass
class TaskStatus:
    """태스크 상태 정보"""
    state: TaskState
    progress: float  # 진행률 (0-100) 