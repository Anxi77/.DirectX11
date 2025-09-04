"""Task item creation and parsing utilities."""
import logging
from typing import Dict, List, Optional, Any

from .models import TaskStatus, TaskPriority, TaskItem

class TaskItemFactory:
    """Factory for creating and parsing task items from GitHub issues."""

    def __init__(self, api_client, config: Dict[str, Any]):
        """Initialize task item factory.

        Args:
            api_client: GitHub API client
            config: Configuration dictionary
        """
        self.api = api_client
        self.config = config
        self.logger = logging.getLogger(__name__)

    def filter_task_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter issues that should be treated as tasks.

        Args:
            issues: List of GitHub issues

        Returns:
            Filtered list of task issues
        """
        filtered_issues = []
        exclude_labels = self.config.get('board_sync', {}).get('exclude_labels', ['DSR'])

        for issue in issues:
            # Skip DSR and other excluded issues
            labels = issue.get('labels', {}).get('nodes', []) if isinstance(issue.get('labels'), dict) else issue.get('labels', [])
            label_names = [label.get('name', '') for label in labels]

            if any(exclude_label in label_names for exclude_label in exclude_labels):
                continue

            # Skip closed issues unless configured otherwise
            if issue.get('state') == 'CLOSED' and not self.config.get('board_sync', {}).get('include_closed', False):
                continue

            filtered_issues.append(issue)

        self.logger.debug(f"Filtered {len(filtered_issues)} task issues from {len(issues)} total issues")
        return filtered_issues

    def create_task_items(self, issues: List[Dict[str, Any]],
                         project_items: Optional[List[Dict[str, Any]]] = None) -> List[TaskItem]:
        """Create TaskItem objects from GitHub issues.

        Args:
            issues: List of GitHub issues
            project_items: Optional list of existing project items

        Returns:
            List of TaskItem objects
        """
        task_items = []
        project_items = project_items or []

        # Create mapping of issue numbers to project items for faster lookup
        project_item_map = {}
        for item in project_items:
            content = item.get('content', {})
            if content and content.get('number'):
                project_item_map[content['number']] = item

        for issue in issues:
            issue_number = issue.get('number')
            if not issue_number:
                continue

            # Extract task information
            status = self.extract_status_from_labels(issue)
            priority = self.extract_priority_from_labels(issue)
            category = self.extract_category_from_labels(issue)
            assignee = None

            # Get assignee information
            assignees = issue.get('assignees', {})
            if isinstance(assignees, dict) and assignees.get('nodes'):
                assignees_list = assignees['nodes']
                if assignees_list:
                    assignee = assignees_list[0].get('login')
            elif isinstance(assignees, list) and assignees:
                assignee = assignees[0].get('login')

            # Get associated project item if exists
            board_item = project_item_map.get(issue_number)

            task_item = TaskItem(
                issue=issue,
                status=status,
                priority=priority,
                category=category,
                assignee=assignee,
                board_item=board_item
            )

            task_items.append(task_item)

        self.logger.debug(f"Created {len(task_items)} task items")
        return task_items

    def extract_status_from_labels(self, issue: Dict[str, Any]) -> TaskStatus:
        """Extract task status from issue labels.

        Args:
            issue: GitHub issue data

        Returns:
            Task status
        """
        labels = issue.get('labels', {}).get('nodes', []) if isinstance(issue.get('labels'), dict) else issue.get('labels', [])

        for label in labels:
            label_name = label.get('name', '').lower()
            if label_name in ['status:todo', 'todo']:
                return TaskStatus.TODO
            elif label_name in ['status:in-progress', 'in-progress', 'in progress']:
                return TaskStatus.IN_PROGRESS
            elif label_name in ['status:in-review', 'in-review', 'review']:
                return TaskStatus.IN_REVIEW
            elif label_name in ['status:done', 'done', 'completed']:
                return TaskStatus.DONE

        # Default based on issue state
        return TaskStatus.DONE if issue.get('state') == 'CLOSED' else TaskStatus.TODO

    def extract_priority_from_labels(self, issue: Dict[str, Any]) -> TaskPriority:
        """Extract task priority from issue labels.

        Args:
            issue: GitHub issue data

        Returns:
            Task priority
        """
        labels = issue.get('labels', {}).get('nodes', []) if isinstance(issue.get('labels'), dict) else issue.get('labels', [])

        for label in labels:
            label_name = label.get('name', '').lower()
            if label_name.startswith('priority:'):
                priority_name = label_name.split(':', 1)[1].upper()
                try:
                    return TaskPriority[priority_name]
                except KeyError:
                    self.logger.warning(f"Unknown priority level: {priority_name}")

        # Default priority
        return TaskPriority.MEDIUM

    def extract_category_from_labels(self, issue: Dict[str, Any]) -> Optional[str]:
        """Extract category from issue labels.

        Args:
            issue: GitHub issue data

        Returns:
            Category name or None
        """
        labels = issue.get('labels', {}).get('nodes', []) if isinstance(issue.get('labels'), dict) else issue.get('labels', [])

        for label in labels:
            label_name = label.get('name', '')
            if label_name.startswith('category:'):
                return label_name.split(':', 1)[1]

        return None
