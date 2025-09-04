"""Business domains for GitHub automation system."""

# Import all domain modules for easy access
from . import commits
from . import issues
from . import projects
from . import reporting

__all__ = ['commits', 'issues', 'projects', 'reporting']
