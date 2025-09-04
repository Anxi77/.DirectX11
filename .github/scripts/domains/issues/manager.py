"""TODO Issue Manager - Creates beautiful individual issues from commit TODO items."""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from infrastructure.api_client import APIClient
from domains.commits.parser import CommitData

@dataclass
class TodoIssueInfo:
    """Information about a created TODO issue."""
    issue_id: str
    issue_number: int
    issue_url: str
    category: str
    task: str
    commit_hash: Optional[str] = None
    dsr_issue_number: Optional[int] = None

class TodoIssueManager:
    """Manages creation of individual GitHub issues from commit TODO items."""

    def __init__(self, api_client: APIClient, config: Dict[str, Any]):
        """Initialize TODO issue manager.

        Args:
            api_client: GitHub API client
            config: Configuration dictionary
        """
        self.api = api_client
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.todo_issue_prefix = config.get('todo_issue_prefix', '📋')
        self.auto_assign = config.get('auto_assign_todos', True)
        self.category_labels = config.get('category_labels', {})
        self.priority_mapping = config.get('todo_priority_mapping', {})

    def create_issues_from_todos(
        self,
        repo_owner: str,
        repo_name: str,
        todos: List[Tuple[str, str]],
        commit_data: Optional[CommitData] = None,
        dsr_issue_number: Optional[int] = None,
        commit_author: Optional[str] = None
    ) -> List[TodoIssueInfo]:
        """Create individual GitHub issues from TODO items.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            todos: List of (category, task) tuples
            commit_data: Associated commit data
            dsr_issue_number: DSR issue number for reference
            commit_author: Commit author username

        Returns:
            List of created TodoIssueInfo objects
        """
        if not todos:
            return []

        self.logger.info(f"Creating {len(todos)} TODO issues")
        created_issues = []

        # Get repository information
        repo_info = self.api.get_repository(repo_owner, repo_name)
        if not repo_info:
            self.logger.error(f"Repository {repo_owner}/{repo_name} not found")
            return []

        repo_id = repo_info['id']

        for category, task in todos:
            try:
                issue_info = self._create_single_todo_issue(
                    repo_id=repo_id,
                    repo_owner=repo_owner,
                    repo_name=repo_name,
                    category=category,
                    task=task,
                    commit_data=commit_data,
                    dsr_issue_number=dsr_issue_number,
                    commit_author=commit_author
                )

                if issue_info:
                    created_issues.append(issue_info)
                    # Note: issue_info could be either newly created or existing issue
                    self.logger.info(f"Processed TODO issue #{issue_info.issue_number}: {task[:50]}...")

            except Exception as e:
                self.logger.error(f"Failed to create TODO issue for '{task}': {e}")
                continue

        self.logger.info(f"Successfully created {len(created_issues)} TODO issues")
        return created_issues

    def _find_existing_todo_issue(self, repo_owner: str, repo_name: str, category: str, task: str) -> Optional[Dict[str, Any]]:
        """Find existing TODO issue with the same task content.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            category: TODO category
            task: Task description

        Returns:
            Existing issue data or None if not found
        """
        try:
            # Get all open issues with 'todo-item' label
            issues = self.api.get_issues(
                repo_owner,
                repo_name,
                state='OPEN',
                labels=['todo-item']
            )

            # Generate expected title for comparison
            expected_title = self._generate_issue_title(category, task)

            # Search for exact title match
            for issue in issues:
                if issue.get('title', '').strip() == expected_title.strip():
                    return issue

            return None

        except Exception as e:
            self.logger.error(f"Error finding existing TODO issue: {e}")
            return None

    def _create_single_todo_issue(
        self,
        repo_id: str,
        repo_owner: str,
        repo_name: str,
        category: str,
        task: str,
        commit_data: Optional[CommitData] = None,
        dsr_issue_number: Optional[int] = None,
        commit_author: Optional[str] = None
    ) -> Optional[TodoIssueInfo]:
        """Create a single TODO issue with beautiful formatting.

        Returns:
            TodoIssueInfo if successful, None otherwise
        """
        # Check if a TODO issue with the same task already exists
        existing_issue = self._find_existing_todo_issue(repo_owner, repo_name, category, task)
        if existing_issue:
            self.logger.info(f"🔄 Reusing existing TODO issue #{existing_issue['number']}: {task[:50]}...")
            return TodoIssueInfo(
                issue_id=existing_issue.get('id', ''),
                issue_number=existing_issue.get('number', 0),
                issue_url=existing_issue.get('url', ''),
                category=category,
                task=task
            )

        # Generate issue title
        title = self._generate_issue_title(category, task)

        # Generate beautiful issue body
        body = self._generate_issue_body(
            category=category,
            task=task,
            commit_data=commit_data,
            dsr_issue_number=dsr_issue_number,
            commit_author=commit_author,
            repo_name=repo_name
        )

        # Generate labels and ensure they exist
        labels = self._generate_issue_labels(category, task)
        label_ids = self._ensure_labels_exist(repo_owner, repo_name, labels)

        # Create the issue
        created_issue = self.api.create_issue_with_assignees(
            repository_id=repo_id,
            title=title,
            body=body,
            labels=label_ids,
            assignees=[commit_author] if commit_author and self.auto_assign else None
        )

        if not created_issue:
            return None

        # Log successful creation of new issue
        self.logger.info(f"✅ Created new TODO issue #{created_issue.get('number', 0)}: {task[:50]}...")

        return TodoIssueInfo(
            issue_id=created_issue.get('id', ''),
            issue_number=created_issue.get('number', 0),
            issue_url=created_issue.get('url', ''),
            category=category,
            task=task,
            commit_hash=commit_data.title if commit_data else None,
            dsr_issue_number=dsr_issue_number
        )

    def _generate_issue_title(self, category: str, task: str) -> str:
        """Generate a beautiful issue title.

        Args:
            category: TODO category
            task: TODO task description

        Returns:
            Formatted issue title
        """
        # Get emoji for category
        category_emoji = self._get_category_emoji(category)

        # Limit task length for title
        task_title = task[:80] + "..." if len(task) > 80 else task

        return f"{self.todo_issue_prefix} [{category}] {task_title}"

    def _generate_issue_body(
        self,
        category: str,
        task: str,
        commit_data: Optional[CommitData] = None,
        dsr_issue_number: Optional[int] = None,
        commit_author: Optional[str] = None,
        repo_name: Optional[str] = None
    ) -> str:
        """Generate beautiful issue body with full context.

        Returns:
            Formatted markdown issue body
        """
        lines = []

        # Header with category emoji
        category_emoji = self._get_category_emoji(category)
        lines.extend([
            f"# {category_emoji} [{category}] Task",
            "",
            f"> **Auto-generated from commit TODO**",
        ])

        if dsr_issue_number:
            lines.append(f"> **DSR Reference:** #{dsr_issue_number}")

        if commit_data:
            lines.append(f"> **Source Commit:** {commit_data.type} - {commit_data.title}")

        lines.extend([
            f"> **Created:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
        ])

        # Task description
        lines.extend([
            "## 📝 Task Description",
            "",
            task,
            "",
        ])

        # Acceptance criteria
        lines.extend([
            "## 🎯 Acceptance Criteria",
            "",
            "- [ ] Task implementation completed",
            "- [ ] Code reviewed and tested",
            "- [ ] Documentation updated if needed",
            "- [ ] Related DSR checkbox marked as complete",
            "",
        ])

        # Context information
        lines.extend([
            "## 🔗 Context Information",
            "",
        ])

        if commit_data:
            lines.extend([
                f"- **Commit Type:** `{commit_data.type}`",
                f"- **Commit Title:** {commit_data.title}",
            ])

            if commit_data.scope:
                lines.append(f"- **Scope:** `{commit_data.scope}`")

            if commit_data.body:
                lines.extend([
                    "",
                    "**Commit Details:**",
                    "",
                ])
                for body_line in commit_data.body:
                    # Check if line already starts with a dash/bullet
                    if body_line.strip().startswith('-'):
                        lines.append(f"{body_line}")
                    else:
                        lines.append(f"- {body_line}")

        if commit_author:
            lines.append(f"- **Author:** @{commit_author}")

        if repo_name:
            lines.append(f"- **Repository:** `{repo_name}`")

        # Footer
        lines.extend([
            "",
            "---",
            "",
            "🤖 *This issue was automatically generated from a commit TODO item.*",
            "",
            f"**Category:** `{category}` • **Priority:** {self._get_priority_badge(category)}",
        ])

        return '\n'.join(lines)

    def _generate_issue_labels(self, category: str, task: str) -> List[str]:
        """Generate appropriate labels for TODO issue.

        Args:
            category: TODO category
            task: TODO task description

        Returns:
            List of label names
        """
        labels = ["todo-item", "automated"]

        # Add category label
        if category.lower() in self.category_labels:
            labels.append(self.category_labels[category.lower()])
        else:
            labels.append(f"category:{category.lower()}")

        # Add priority label based on category
        priority = self._get_task_priority(category, task)
        if priority:
            labels.append(f"priority:{priority}")

        # Add type labels based on keywords
        task_lower = task.lower()
        if any(word in task_lower for word in ['bug', 'fix', 'error', 'issue']):
            labels.append('type:bug')
        elif any(word in task_lower for word in ['feature', 'add', 'implement']):
            labels.append('type:enhancement')
        elif any(word in task_lower for word in ['test', 'testing', 'coverage']):
            labels.append('type:testing')
        elif any(word in task_lower for word in ['docs', 'documentation', 'readme']):
            labels.append('type:documentation')

        return labels

    def _ensure_labels_exist(self, repo_owner: str, repo_name: str, label_names: List[str]) -> List[str]:
        """Ensure all labels exist in the repository, creating them if necessary.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            label_names: List of label names to ensure exist

        Returns:
            List of label IDs for existing/created labels
        """
        label_ids = []

        # Define default colors and descriptions for different label types
        label_defaults = {
            'todo-item': {'color': '0E8A16', 'description': 'TODO item extracted from commit'},
            'automated': {'color': '7057FF', 'description': 'Automatically generated'},
            'DSR': {'color': 'D73A49', 'description': 'Daily Status Report'},
            'type:bug': {'color': 'D73A49', 'description': 'Bug fixes'},
            'type:enhancement': {'color': 'A2EEEF', 'description': 'New features'},
            'type:testing': {'color': 'FBCA04', 'description': 'Testing related'},
            'type:documentation': {'color': '0052CC', 'description': 'Documentation updates'},
        }

        for label_name in label_names:
            # Get or create the label
            defaults = label_defaults.get(label_name, {'color': '0969da', 'description': f'Auto-generated label: {label_name}'})

            # Handle priority labels
            if label_name.startswith('priority:'):
                priority = label_name.split(':')[1]
                priority_colors = {
                    'low': '0E8A16',
                    'medium': 'FBCA04',
                    'high': 'FF6900',
                    'critical': 'D73A49'
                }
                defaults = {
                    'color': priority_colors.get(priority, '0969da'),
                    'description': f'Priority: {priority.title()}'
                }

            # Handle category labels
            elif label_name.startswith('category:'):
                defaults = {
                    'color': '5319E7',
                    'description': f'Category: {label_name.split(":")[1].title()}'
                }

            label_id = self.api.get_or_create_label(
                repo_owner,
                repo_name,
                label_name,
                defaults['color'],
                defaults['description']
            )

            if label_id:
                label_ids.append(label_id)
            else:
                self.logger.warning(f"Failed to get or create label: {label_name}")

        return label_ids

    def _get_category_emoji(self, category: str) -> str:
        """Get emoji for TODO category.

        Args:
            category: TODO category name

        Returns:
            Appropriate emoji
        """
        category_emojis = {
            'security': '🛡️',
            'performance': '⚡',
            'testing': '🧪',
            'documentation': '📚',
            'ui': '🎨',
            'ux': '👥',
            'api': '🔌',
            'database': '🗄️',
            'deployment': '🚀',
            'monitoring': '📊',
            'refactoring': '♻️',
            'maintenance': '🔧',
            'feature': '✨',
            'bugfix': '🐛',
            'enhancement': '📈',
            'cleanup': '🧹',
            'optimization': '🔄',
        }

        return category_emojis.get(category.lower(), '📋')

    def _get_priority_badge(self, category: str) -> str:
        """Get priority badge for category.

        Args:
            category: TODO category

        Returns:
            Priority badge emoji
        """
        high_priority_categories = {'security', 'bugfix', 'critical'}
        medium_priority_categories = {'performance', 'testing', 'api'}

        if category.lower() in high_priority_categories:
            return "🔴 High"
        elif category.lower() in medium_priority_categories:
            return "🟡 Medium"
        else:
            return "🟢 Normal"

    def _get_task_priority(self, category: str, task: str) -> Optional[str]:
        """Determine task priority based on category and content.

        Args:
            category: TODO category
            task: Task description

        Returns:
            Priority level string or None
        """
        task_lower = task.lower()

        # High priority indicators
        if (category.lower() in ['security', 'critical', 'bugfix'] or
            any(word in task_lower for word in ['urgent', 'critical', 'security', 'vulnerability'])):
            return 'high'

        # Medium priority indicators
        if (category.lower() in ['performance', 'testing', 'api'] or
            any(word in task_lower for word in ['performance', 'optimize', 'test', 'important'])):
            return 'medium'

        # Low priority for documentation, cleanup, etc.
        if category.lower() in ['documentation', 'cleanup', 'maintenance']:
            return 'low'

        return None

    def get_todo_issue_status(self, repo_owner: str, repo_name: str, issue_numbers: List[int]) -> Dict[int, str]:
        """Get status of TODO issues for DSR synchronization.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            issue_numbers: List of issue numbers to check

        Returns:
            Dictionary mapping issue numbers to their states ('open', 'closed')
        """
        if not issue_numbers:
            return {}

        status_map = {}

        for issue_number in issue_numbers:
            try:
                issue = self.api.get_issue(repo_owner, repo_name, issue_number)
                if issue:
                    status_map[issue_number] = issue.get('state', 'open').lower()
                else:
                    # Issue not found, consider it closed
                    status_map[issue_number] = 'closed'

            except Exception as e:
                self.logger.warning(f"Failed to get status for issue #{issue_number}: {e}")
                status_map[issue_number] = 'open'  # Default to open on error

        return status_map

    def sync_dsr_checkboxes(self, dsr_issue_id: str, issue_links: Dict[str, int]) -> bool:
        """Synchronize DSR checkboxes based on linked issue statuses.

        Args:
            dsr_issue_id: DSR issue ID
            issue_links: Dictionary mapping task descriptions to issue numbers

        Returns:
            True if sync was successful
        """
        try:
            # Get current DSR issue
            dsr_issue = self.api.get_issue_by_id(dsr_issue_id)
            if not dsr_issue:
                self.logger.error(f"DSR issue {dsr_issue_id} not found")
                return False

            # Get linked issue statuses
            issue_numbers = list(issue_links.values())
            repo_owner = dsr_issue.get('repository', {}).get('owner', {}).get('login', '')
            repo_name = dsr_issue.get('repository', {}).get('name', '')

            if not repo_owner or not repo_name:
                self.logger.error("Could not determine repository from DSR issue")
                return False

            status_map = self.get_todo_issue_status(repo_owner, repo_name, issue_numbers)

            # Update DSR issue body with synchronized checkboxes
            current_body = dsr_issue.get('body', '')
            self.logger.info(f"🔄 Updating checkboxes for {len(issue_links)} linked issues")
            updated_body = self._update_dsr_checkboxes(current_body, issue_links, status_map)
            
            # Update category statistics (e.g., "0/5" counters)
            self.logger.info(f"📊 Updating category statistics...")
            updated_body = self._update_category_statistics(updated_body)

            if updated_body != current_body:
                success = self.api.update_issue(dsr_issue_id, body=updated_body)
                if success:
                    self.logger.info(f"Synchronized DSR checkboxes and category statistics for issue {dsr_issue_id}")
                    return True
                else:
                    self.logger.error(f"Failed to update DSR issue {dsr_issue_id}")
                    return False

            return True  # No changes needed

        except Exception as e:
            self.logger.error(f"Failed to sync DSR checkboxes: {e}")
            return False

    def _update_dsr_checkboxes(self, dsr_body: str, issue_links: Dict[str, int], status_map: Dict[int, str]) -> str:
        """Update checkbox states in DSR body based on issue statuses.

        Args:
            dsr_body: Current DSR issue body
            issue_links: Task descriptions mapped to issue numbers
            status_map: Issue numbers mapped to their states

        Returns:
            Updated DSR body with synchronized checkboxes
        """
        lines = dsr_body.split('\n')
        updated_lines = []

        for line in lines:
            # Look for checkbox lines with issue links in new format: "- [] #123"
            if line.strip().startswith('- ['):
                import re
                # Check for new format: "- [] #123" or "- [x] #123"
                new_format_match = re.match(r'^(\s*- \[)(x?)\] #(\d+)', line)
                if new_format_match:
                    issue_number = int(new_format_match.group(3))
                    if issue_number in status_map:
                        # Update checkbox based on issue status
                        if status_map[issue_number] == 'closed':
                            # Mark as completed
                            line = re.sub(r'- \[\]', '- [x]', line)
                        else:
                            # Mark as incomplete
                            line = re.sub(r'- \[x\]', '- []', line)
                # Also support old format for backward compatibility: "- [ ] Task (#123)"
                elif '(#' in line:
                    issue_match = re.search(r'\(#(\d+)\)', line)
                    if issue_match:
                        issue_number = int(issue_match.group(1))
                        if issue_number in status_map:
                            # Update checkbox based on issue status
                            if status_map[issue_number] == 'closed':
                                # Mark as completed
                                line = re.sub(r'- \[ \]', '- [x]', line)
                            else:
                                # Mark as incomplete
                                line = re.sub(r'- \[x\]', '- [ ]', line)

            updated_lines.append(line)

        return '\n'.join(updated_lines)

    def _update_category_statistics(self, dsr_body: str) -> str:
        """Update category statistics (e.g., '0/5' counters) in DSR body.
        
        Args:
            dsr_body: DSR issue body content
            
        Returns:
            Updated DSR body with corrected category statistics
        """
        import re
        
        self.logger.info("📊 Starting category statistics update...")
        
        lines = dsr_body.split('\n')
        updated_lines = []
        current_category = None
        category_stats = {}
        
        # First pass: identify categories and count todos
        self.logger.info("🔍 First pass: scanning for categories and checkboxes...")
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect category headers in DSR format: "<summary><strong>category</strong> (0/5 completed)</summary>"
            category_match = re.match(r'^<summary><strong>([^<]+)</strong>\s*\((\d+)/(\d+)\s*completed\)</summary>', stripped)
            if category_match:
                category_name = category_match.group(1).strip()
                old_completed = int(category_match.group(2))
                old_total = int(category_match.group(3))
                current_category = category_name
                category_stats[category_name] = {'completed': 0, 'total': 0}
                self.logger.info(f"   Found category '{category_name}' at line {i+1}: currently shows {old_completed}/{old_total}")
                continue
            
            # Count checkboxes under current category
            if current_category and stripped.startswith('- ['):
                category_stats[current_category]['total'] += 1
                checkbox_state = 'completed' if '- [x]' in stripped else 'pending'
                if '- [x]' in stripped:
                    category_stats[current_category]['completed'] += 1
                
                self.logger.info(f"   Line {i+1} in '{current_category}': {checkbox_state} - '{stripped[:50]}...'")
        
        self.logger.info("📈 Category statistics calculated:")
        for category, stats in category_stats.items():
            self.logger.info(f"   {category}: {stats['completed']}/{stats['total']} completed")
        
        # Second pass: update category statistics
        self.logger.info("✏️  Second pass: updating category headers...")
        
        current_category = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Update category headers with correct counts
            category_match = re.match(r'^<summary><strong>([^<]+)</strong>\s*\(\d+/\d+\s*completed\)</summary>', stripped)
            if category_match:
                category_name = category_match.group(1).strip()
                current_category = category_name
                
                if category_name in category_stats:
                    completed = category_stats[category_name]['completed']
                    total = category_stats[category_name]['total']
                    
                    # Update the line with correct counts in DSR format
                    updated_line = f"<summary><strong>{category_name}</strong> ({completed}/{total} completed)</summary>"
                    updated_lines.append(updated_line)
                    
                    # Log the update for debugging
                    try:
                        old_completed = int(re.search(r'\((\d+)/', line).group(1))
                        old_total = int(re.search(r'/(\d+)\)', line).group(1))
                        if completed != old_completed or total != old_total:
                            self.logger.info(f"   ✅ Updated line {i+1} '{category_name}': {old_completed}/{old_total} → {completed}/{total}")
                        else:
                            self.logger.info(f"   ➡️  No change for '{category_name}': {completed}/{total}")
                    except (AttributeError, ValueError):
                        self.logger.info(f"   ✅ Updated line {i+1} '{category_name}': → {completed}/{total}")
                else:
                    self.logger.warning(f"   ⚠️  Category '{category_name}' found in header but no stats calculated")
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        result = '\n'.join(updated_lines)
        self.logger.info("📊 Category statistics update completed")
        
        return result

def create_todo_issues(api_client: APIClient, config: Dict[str, Any],
                      repo_owner: str, repo_name: str,
                      todos: List[Tuple[str, str]],
                      commit_data: Optional[CommitData] = None,
                      dsr_issue_number: Optional[int] = None,
                      commit_author: Optional[str] = None) -> List[TodoIssueInfo]:
    """Create TODO issues using the TodoIssueManager.

    This is a convenience function that maintains backward compatibility
    with the original standalone script interface.

    Args:
        api_client: GitHub API client
        config: Configuration dictionary
        repo_owner: Repository owner
        repo_name: Repository name
        todos: List of (category, task) tuples
        commit_data: Associated commit data
        dsr_issue_number: DSR issue number for reference
        commit_author: Commit author username

    Returns:
        List of created TodoIssueInfo objects
    """
    manager = TodoIssueManager(api_client, config)
    return manager.create_issues_from_todos(
        repo_owner=repo_owner,
        repo_name=repo_name,
        todos=todos,
        commit_data=commit_data,
        dsr_issue_number=dsr_issue_number,
        commit_author=commit_author
    )
