"""GitHub Automation System."""

__version__ = "2.0.0"
__author__ = "GitHub Automation"
__description__ = "Streamlined GitHub automation for DSR generation and project management"

# Domain components
from .infrastructure.api_client import APIClient
from .domains.commits import CommitParser, CommitData
from .domains.reporting import DailyReporter, TodoItem, BranchSummary
from .domains.projects import BoardSync, TaskStatus, TaskPriority, TaskItem
from .domains.issues import TodoIssueManager, TodoIssueInfo

__all__ = [
    # Infrastructure
    'APIClient',
    # Commits domain
    'CommitParser',
    'CommitData',
    # Reporting domain
    'DailyReporter', 
    'TodoItem',
    'BranchSummary',
    # Projects domain
    'BoardSync',
    'TaskStatus',
    'TaskPriority', 
    'TaskItem',
    # Issues domain
    'TodoIssueManager',
    'TodoIssueInfo',
]
