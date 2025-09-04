"""Streamlined board synchronization - core functionality only."""
import logging
import time
from typing import Dict, List, Optional, Any

from infrastructure.api_client import APIClient
from .models import TaskStatus, TaskItem
from .task_factory import TaskItemFactory
from .field_manager import ProjectFieldManager
from .todo_sync import TodoSync

class BoardSync:
    """Streamlined project board synchronization."""

    def __init__(self, api_client: APIClient, config: Dict[str, Any], repo_owner: str, repo_name: str):
        """Initialize board synchronizer.

        Args:
            api_client: API client
            config: Configuration dictionary
            repo_owner: Repository owner/organization
            repo_name: Repository name
        """
        self.api = api_client
        self.config = config
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.logger = logging.getLogger(__name__)

        # Initialize project connection
        self.project_id: Optional[str] = None
        self.project_number: Optional[int] = None
        self.project_enabled = False

        # Initialize helper classes
        self.task_factory = TaskItemFactory(api_client, config)
        self.field_manager: Optional[ProjectFieldManager] = None
        self.todo_sync: Optional[TodoSync] = None

        # Try to initialize project
        if self.initialize_project():
            self.field_manager = ProjectFieldManager(api_client, self.project_id, repo_owner)
            self.todo_sync = TodoSync(api_client, config, self.project_id, repo_owner, self.project_number)

    def initialize_project(self) -> bool:
        """Initialize project connection.

        Returns:
            True if project initialization was successful
        """
        try:
            # Try to get or create project by repository name
            project_name = self.repo_name
            self.logger.info(f"Looking for project '{project_name}' in {self.repo_owner}")
            
            project_info = self.api.get_or_create_project_by_name(self.repo_owner, project_name)
            if not project_info:
                self.logger.error(f"Failed to get or create project '{project_name}'")
                return False

            self.project_id = project_info.get('id')
            self.project_number = project_info.get('number')
            
            if not self.project_id or not self.project_number:
                self.logger.error("Could not get project ID or number")
                return False

            self.project_enabled = True
            self.logger.info(f"Initialized project board connection: '{project_name}' (#{self.project_number})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize project: {e}")
            return False

    def sync_board(self, repo_owner: str = None, repo_name: str = None) -> Dict[str, Any]:
        """Synchronize project board with repository issues.

        Args:
            repo_owner: Repository owner (optional, uses instance default)
            repo_name: Repository name (optional, uses instance default)

        Returns:
            Sync results dictionary
        """
        if not self.project_enabled:
            return {'success': False, 'error': 'Project board not initialized'}

        # Use provided parameters or fall back to instance defaults
        repo_owner = repo_owner or self.repo_owner
        repo_name = repo_name or self.repo_name

        try:
            self.logger.info(f"Starting board sync for {repo_owner}/{repo_name}")

            # Get repository issues
            issues = self.api.get_issues(repo_owner, repo_name, state='OPEN')
            if not issues:
                self.logger.info("No issues found in repository")
                return {'success': True, 'synced_issues': 0, 'created_items': 0}

            # Filter task issues (exclude DSR and other non-task issues)
            task_issues = self.task_factory.filter_task_issues(issues)

            # Get existing project items
            project_items = self.api.get_project_items(self.project_id)

            # Create task items from issues
            task_items = self.task_factory.create_task_items(task_issues, project_items)

            # Sync task items to project board
            results = self._sync_task_items(task_items)

            # Update project metrics
            self._update_project_metrics(task_items)

            self.logger.info(f"Board sync completed: {results}")
            return {'success': True, **results}

        except Exception as e:
            self.logger.error(f"Error during board sync: {e}")
            return {'success': False, 'error': str(e)}

    def sync_todo_issues(self) -> bool:
        """Sync TODO issues to project board.

        Returns:
            True if sync was successful
        """
        if not self.todo_sync:
            self.logger.error("TODO sync not available - project not initialized")
            return False

        return self.todo_sync.sync_todo_issues(self.repo_owner, self.repo_name)

    def update_task_status(self, repo_owner: str, repo_name: str, issue_number: int,
                          new_status: TaskStatus) -> bool:
        """Update task status for an issue (GitHub handles project item sync automatically).

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            issue_number: Issue number to update
            new_status: New task status

        Returns:
            True if update was successful
        """
        if not self.project_enabled:
            self.logger.error("Project board not initialized")
            return False

        try:
            # Get issue information
            issue = self.api.get_issue(repo_owner, repo_name, issue_number)
            if not issue:
                self.logger.error(f"Issue #{issue_number} not found")
                return False

            # Note: GitHub automatically syncs project item status when issue state changes
            # Manual status updates should be done through GitHub UI or direct issue state changes
            self.logger.info(f"Issue #{issue_number} found - GitHub will auto-sync project item status")
            return True

        except Exception as e:
            self.logger.error(f"Failed to validate issue: {e}")
            return False

    def get_project_statistics(self, repo_owner: str, repo_name: str) -> Dict[str, Any]:
        """Get project statistics.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name

        Returns:
            Project statistics dictionary
        """
        if not self.project_enabled:
            return {'error': 'Project board not initialized'}

        try:
            # Get project items
            project_items = self.api.get_project_items(self.project_id)

            # Get repository issues
            issues = self.api.get_issues(repo_owner, repo_name, state='ALL')
            task_issues = self.task_factory.filter_task_issues(issues)

            # Create task items for analysis
            task_items = self.task_factory.create_task_items(task_issues, project_items)

            # Calculate statistics
            stats = {
                'total_issues': len(task_issues),
                'project_items': len(project_items),
                'status_breakdown': {},
                'priority_breakdown': {},
                'category_breakdown': {}
            }

            # Analyze task items
            for task_item in task_items:
                # Status breakdown
                status = task_item.status.value
                stats['status_breakdown'][status] = stats['status_breakdown'].get(status, 0) + 1

                # Priority breakdown
                priority = task_item.priority.value
                stats['priority_breakdown'][priority] = stats['priority_breakdown'].get(priority, 0) + 1

                # Category breakdown
                category = task_item.category or 'Uncategorized'
                stats['category_breakdown'][category] = stats['category_breakdown'].get(category, 0) + 1

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get project statistics: {e}")
            return {'error': str(e)}

    def _sync_task_items(self, task_items: List[TaskItem]) -> Dict[str, Any]:
        """Sync task items to project board.

        Args:
            task_items: List of task items to sync

        Returns:
            Sync results
        """
        synced_count = 0
        created_count = 0
        failed_count = 0

        for task_item in task_items:
            try:
                if task_item.board_item:
                    # Update existing project item
                    if self._update_project_item(task_item):
                        synced_count += 1
                    else:
                        failed_count += 1
                else:
                    # Create new project item
                    if self._create_project_item(task_item):
                        created_count += 1
                    else:
                        failed_count += 1

                # Small delay to avoid rate limiting
                time.sleep(0.2)

            except Exception as e:
                self.logger.error(f"Failed to sync task item: {e}")
                failed_count += 1

        return {
            'synced_issues': synced_count,
            'created_items': created_count,
            'failed_items': failed_count
        }

    def _update_project_item(self, task_item: TaskItem) -> bool:
        """Update existing project item (custom fields only - Status is auto-managed by GitHub).

        Args:
            task_item: Task item to update

        Returns:
            True if update was successful
        """
        try:
            item_id = task_item.board_item.get('id')
            if not item_id:
                return False

            # Only update custom fields (Category, Priority)
            # Status is automatically managed by GitHub when issue state changes
            success = True
            
            if task_item.category and self.field_manager:
                self.field_manager.ensure_category_field_exists(task_item.category)
                field_success = self.api.update_project_item_field(
                    project_id=self.project_id,
                    item_id=item_id,
                    field_name="Category",
                    field_value=task_item.category
                )
                success = success and field_success

            return success

        except Exception as e:
            self.logger.error(f"Failed to update project item: {e}")
            return False

    def _create_project_item(self, task_item: TaskItem) -> bool:
        """Create new project item (Status auto-managed by GitHub).

        Args:
            task_item: Task item to create

        Returns:
            True if creation was successful
        """
        try:
            # Create the project item (GitHub will auto-set Status based on issue state)
            created_item = self.api.create_project_item(
                project_id=self.project_id,
                content_id=task_item.issue['id']
            )

            if not created_item:
                return False

            # Set only custom fields (GitHub auto-manages Status field)
            item_id = created_item.get('id')
            if item_id and task_item.category and self.field_manager:
                self.field_manager.ensure_category_field_exists(task_item.category)
                self.api.update_project_item_field(
                    project_id=self.project_id,
                    item_id=item_id,
                    field_name="Category",
                    field_value=task_item.category
                )

            return True

        except Exception as e:
            self.logger.error(f"Failed to create project item: {e}")
            return False

    # Removed: _update_issue_labels() - Labels managed manually, project status auto-synced by GitHub

    # Removed: _update_project_item_status() - GitHub automatically syncs project item status with issue state

    def _update_project_metrics(self, task_items: List[TaskItem]):
        """Update project metrics.

        Args:
            task_items: List of task items for metrics calculation
        """
        try:
            # Calculate basic metrics
            total_items = len(task_items)
            completed_items = sum(1 for item in task_items if item.status == TaskStatus.DONE)

            completion_rate = (completed_items / total_items * 100) if total_items > 0 else 0

            self.logger.info(f"Project metrics: {total_items} total items, "
                           f"{completed_items} completed ({completion_rate:.1f}%)")

        except Exception as e:
            self.logger.error(f"Failed to update project metrics: {e}")

# Backward compatibility function
def run_todo_sync(api_client: APIClient, config: Dict[str, Any], repo_owner: str, repo_name: str) -> bool:
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
        sync = BoardSync(api_client, config, repo_owner, repo_name)
        return sync.sync_todo_issues()
    except Exception as e:
        logging.error(f"Error in run_todo_sync: {e}")
        return False
