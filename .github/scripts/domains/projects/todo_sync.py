"""TODO-specific project synchronization utilities."""
import logging
import time
from typing import Dict, List, Optional, Any

from .models import TaskStatus, TaskPriority, TaskItem
from .field_manager import ProjectFieldManager

class TodoSync:
    """Handles synchronization of TODO issues with project boards."""

    def __init__(self, api_client, config: Dict[str, Any], project_id: str, project_owner: str, project_number: int):
        """Initialize TODO synchronizer.

        Args:
            api_client: GitHub API client
            config: Configuration dictionary
            project_id: GitHub project ID
            project_owner: Project owner
            project_number: GitHub project number
        """
        self.api = api_client
        self.config = config
        self.project_id = project_id
        self.project_owner = project_owner
        self.project_number = project_number
        self.logger = logging.getLogger(__name__)
        self.field_manager = ProjectFieldManager(api_client, project_id, project_owner)

    def sync_todo_issues(self, repo_owner: str, repo_name: str) -> bool:
        """Find and sync all TODO issues to project board.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name

        Returns:
            True if sync was successful, False otherwise
        """
        project_config = self.config.get('project_sync', {})
        if not project_config.get('enabled', False):
            self.logger.info("Project board sync is disabled")
            return True

        try:
            # Find all TODO issues
            todo_issues = self._find_todo_issues(repo_owner, repo_name)

            if not todo_issues:
                self.logger.info("No TODO issues found to sync")
                return True

            self.logger.info(f"Found {len(todo_issues)} TODO issues to sync")

            # Sync each issue to project board
            synced_count = 0
            failed_count = 0

            for issue in todo_issues:
                try:
                    if self._sync_todo_issue_to_project(issue, repo_owner, repo_name):
                        synced_count += 1
                        # Detailed logging is done within _sync_todo_issue_to_project method
                    else:
                        failed_count += 1
                        self.logger.warning(f"Failed to sync issue #{issue['number']} to project board")

                    # Small delay to avoid rate limiting
                    time.sleep(0.5)

                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"Error syncing issue #{issue['number']}: {e}")

            self.logger.info(f"TODO sync completed: {synced_count} processed (new + existing), {failed_count} failed")
            return failed_count == 0

        except Exception as e:
            self.logger.error(f"Error during TODO sync: {e}")
            return False

    def _find_todo_issues(self, repo_owner: str, repo_name: str) -> List[Dict[str, Any]]:
        """Find all issues with 'todo-item' label.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name

        Returns:
            List of TODO issues
        """
        try:
            # Get all open issues with 'todo-item' label
            issues = self.api.get_issues(
                repo_owner,
                repo_name,
                state='OPEN',
                labels=['todo-item']
            )

            return issues

        except Exception as e:
            self.logger.error(f"Error finding TODO issues: {e}")
            return []

    def _sync_todo_issue_to_project(self, issue: Dict[str, Any], repo_owner: str, repo_name: str) -> bool:
        """Sync a single TODO issue to project board.

        Args:
            issue: GitHub issue data
            repo_owner: Repository owner
            repo_name: Repository name

        Returns:
            True if sync was successful
        """
        try:
            issue_number = issue['number']

            # Check if issue is already in project
            if self._is_todo_issue_in_project(issue_number):
                self.logger.info(f"⏭️ Issue #{issue_number} already exists in project board - skipping")
                return True

            # Extract category from labels (for TaskItem only, not used for project fields)
            category = self._extract_category_from_issue(issue)

            # Determine priority from labels
            priority = self._extract_priority_from_issue(issue)

            # Create TaskItem
            task_item = TaskItem(
                issue=issue,
                status=TaskStatus.TODO,
                priority=priority,
                category=category,
                assignee=None
            )

            # Add to project board
            project_data = {'id': self.project_id, 'owner': self.project_owner}
            success = self._create_project_item(project_data, task_item)

            if success:
                self.logger.info(f"✅ Added new TODO issue #{issue_number} to project board with status 'Todo'")

            return success

        except Exception as e:
            self.logger.error(f"Error syncing TODO issue to project: {e}")
            return False

    def _is_todo_issue_in_project(self, issue_number: int) -> bool:
        """Check if issue is already in project board.

        Args:
            issue_number: GitHub issue number

        Returns:
            True if issue is in project
        """
        try:
            # Get project items and check if issue is already there
            project_items = self.api.get_project_items(self.project_id)

            for item in project_items:
                content = item.get('content', {})
                if content.get('number') == issue_number:
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking if issue #{issue_number} is in project: {e}")
            return False

    def _extract_category_from_issue(self, issue: Dict[str, Any]) -> Optional[str]:
        """Extract category from issue labels.

        Args:
            issue: GitHub issue data

        Returns:
            Category name or None
        """
        labels = issue.get('labels', [])

        # Handle both REST API format (list of dicts) and GraphQL format (dict with nodes)
        if isinstance(labels, dict) and 'nodes' in labels:
            labels = labels['nodes']

        for label in labels:
            label_name = label.get('name', '')
            if label_name.startswith('category:'):
                return label_name.split(':', 1)[1]

        return None

    def _extract_priority_from_issue(self, issue: Dict[str, Any]) -> TaskPriority:
        """Extract priority from issue labels.

        Args:
            issue: GitHub issue data

        Returns:
            Task priority
        """
        labels = issue.get('labels', [])

        # Handle both REST API format (list of dicts) and GraphQL format (dict with nodes)
        if isinstance(labels, dict) and 'nodes' in labels:
            labels = labels['nodes']

        for label in labels:
            label_name = label.get('name', '')
            if label_name.startswith('priority:'):
                priority_name = label_name.split(':', 1)[1].upper()
                try:
                    return TaskPriority[priority_name]
                except KeyError:
                    self.logger.warning(f"Unknown priority level: {priority_name}")

        # Default priority
        return TaskPriority.MEDIUM

    def _create_project_item(self, project_data: Dict[str, Any], task_item: TaskItem) -> bool:
        """Create a new project item from task item.

        Args:
            project_data: Project information
            task_item: Task item to create

        Returns:
            True if creation was successful
        """
        try:
            # Create the project item
            created_item = self.api.create_project_item(
                project_id=self.project_id,
                content_id=task_item.issue['id']
            )

            if not created_item:
                return False

            # Update any additional fields if needed
            item_id = created_item.get('id')
            if item_id:
                # Set status field to "Todo"
                try:
                    status_field_id = self.api.get_field_id_by_name(
                        self.project_owner, self.project_number, "Status"
                    )
                    if status_field_id:
                        status_option_id = self.api.get_select_option_id(
                            self.project_owner, self.project_number, "Status", "Todo"
                        )
                        if status_option_id:
                            self.api.update_item_field(
                                self.project_id, item_id, status_field_id, {"singleSelectOptionId": status_option_id}
                            )
                            self.logger.debug(f"Set status to 'Todo' for item {item_id}")
                        else:
                            self.logger.warning(f"Could not find 'Todo' option in Status field")
                    else:
                        self.logger.warning(f"Could not find Status field in project")
                except Exception as e:
                    self.logger.warning(f"Failed to set status for item {item_id}: {e}")

                # Note: Category field setting removed due to API complexity
                # Project items will only have Status set to "Todo"

            return True

        except Exception as e:
            self.logger.error(f"Failed to create project item: {e}")
            return False

def run_todo_sync(api_client, config: Dict[str, Any], repo_owner: str, repo_name: str) -> bool:
    """Run TODO project synchronization.

    Args:
        api_client: GitHub API client
        config: Configuration dictionary
        repo_owner: Repository owner
        repo_name: Repository name

    Returns:
        True if sync was successful
    """
    try:
        # Get project information
        project_config = config.get('project_sync', {})
        project_number = project_config.get('project_number')

        if not project_number:
            logging.error("No project number configured for TODO sync")
            return False

        # Get project ID
        project_info = api_client.get_project_by_number(repo_owner, project_number)
        if not project_info:
            logging.error(f"Project #{project_number} not found")
            return False

        project_id = project_info.get('id')
        if not project_id:
            logging.error("Could not get project ID")
            return False

        # Initialize and run TODO sync
        todo_sync = TodoSync(api_client, config, project_id, repo_owner, project_number)
        return todo_sync.sync_todo_issues(repo_owner, repo_name)

    except Exception as e:
        logging.error(f"Error in run_todo_sync: {e}")
        return False
