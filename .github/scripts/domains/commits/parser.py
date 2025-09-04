"""Commit message parser for [type] format with Body/Todo/Footer sections."""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class CommitData:
    """Parsed commit data structure."""
    type: str
    scope: Optional[str]
    title: str
    body: List[str]
    todos: List[Tuple[str, str]]  # (category, task)
    footer: List[str]
    breaking: bool = False
    author: Optional[str] = None
    timestamp: Optional[str] = None
    time: Optional[str] = None  # HH:MM:SS format for display
    hash: Optional[str] = None

class CommitParser:
    """Parse commit messages following [type] convention."""

    COMMIT_TYPES = {
        'feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore',
        'design', 'comment', 'rename', 'remove', 'debug', '!BREAKING CHANGE', '!HOTFIX'
    }

    def __init__(self):
        # Pattern for [type(scope)] title format
        self.title_pattern = re.compile(
            r'^\[([^(\]]+)(?:\(([^)]+)\))?\]\s*(.+)$'
        )

        # Patterns for sections
        self.section_patterns = {
            'body': re.compile(r'^\[Body\]\s*$', re.IGNORECASE),
            'todo': re.compile(r'^\[Todo\]\s*$', re.IGNORECASE),
            'footer': re.compile(r'^\[Footer\]\s*$', re.IGNORECASE)
        }

        # Todo patterns
        self.todo_category_pattern = re.compile(r'^@(.+?)\s*$')
        self.todo_item_pattern = re.compile(r'^-\s+(.+)$')

    def parse(self, commit_message: str) -> CommitData:
        """Parse a commit message into structured data.

        Args:
            commit_message: Raw commit message text

        Returns:
            CommitData object with parsed structure

        Raises:
            ValueError: If commit format is invalid
        """
        lines = commit_message.strip().split('\n')

        if not lines:
            raise ValueError("Empty commit message")

        # Parse title line
        title_line = lines[0].strip()
        match = self.title_pattern.match(title_line)

        if not match:
            raise ValueError(f"Invalid commit title format: {title_line}")

        commit_type_raw = match.group(1).strip()
        scope = match.group(2)
        title = match.group(3).strip()

        # Handle special types (with !) vs normal types (lowercase)
        if commit_type_raw.startswith('!'):
            commit_type = commit_type_raw.upper()
        else:
            commit_type = commit_type_raw.lower()

        # Validate commit type
        if commit_type not in self.COMMIT_TYPES:
            raise ValueError(f"Invalid commit type: {commit_type}")

        # Parse sections
        body_lines = []
        todo_items = []
        footer_lines = []

        current_section = None
        current_category = None

        for line in lines[1:]:
            line = line.strip()

            # Check for section headers
            section_found = False
            for section_name, pattern in self.section_patterns.items():
                if pattern.match(line):
                    current_section = section_name
                    section_found = True
                    break

            if section_found:
                continue

            # Skip empty lines
            if not line:
                continue

            # Process content based on current section
            if current_section == 'body':
                body_lines.append(line)
            elif current_section == 'todo':
                current_category = self._parse_todo_line(line, todo_items, current_category)
            elif current_section == 'footer':
                footer_lines.append(line)

        return CommitData(
            type=commit_type,
            scope=scope,
            title=title,
            body=body_lines,
            todos=todo_items,
            footer=footer_lines,
            breaking=commit_type.startswith('!')
        )

    def _parse_todo_line(self, line: str, todo_items: List[Tuple[str, str]],
                        current_category: Optional[str]) -> Optional[str]:
        """Parse a todo line and add to todo_items.

        Returns:
            Updated current_category if category line found
        """
        # Check for category line
        category_match = self.todo_category_pattern.match(line)
        if category_match:
            return category_match.group(1)

        # Check for todo item
        todo_match = self.todo_item_pattern.match(line)
        if todo_match:
            category = current_category or 'General'
            task = todo_match.group(1)
            todo_items.append((category, task))

        return current_category

    def format_commit(self, data: CommitData) -> str:
        """Format CommitData back into commit message.

        Args:
            data: CommitData to format

        Returns:
            Formatted commit message string
        """
        lines = []

        # Format title
        title = f"[{data.type}"
        if data.scope:
            title += f"({data.scope})"
        title += f"] {data.title}"
        lines.append(title)

        # Add empty line if there are additional sections
        if data.body or data.todos or data.footer:
            lines.append("")

        # Add body section
        if data.body:
            lines.append("[Body]")
            lines.extend(data.body)
            lines.append("")

        # Add todo section
        if data.todos:
            lines.append("[Todo]")
            current_category = None

            for category, task in data.todos:
                if category != current_category:
                    lines.append(f"{category}")
                    current_category = category
                lines.append(f"- {task}")

            lines.append("")

        # Add footer section
        if data.footer:
            lines.append("[Footer]")
            lines.extend(data.footer)

        return '\n'.join(lines).rstrip()

    def extract_issue_references(self, data: CommitData) -> Dict[str, List[str]]:
        """Extract issue references from commit data.

        Returns:
            Dictionary with 'closes', 'fixes', and 'related' keys
        """
        references = {
            'closes': [],
            'fixes': [],
            'related': []
        }

        # Check footer for issue references
        for line in data.footer:
            line_lower = line.lower().strip()

            # Extract issue numbers
            issue_nums = re.findall(r'#(\d+)', line)

            if line_lower.startswith('closes'):
                references['closes'].extend(issue_nums)
            elif line_lower.startswith('fixes'):
                references['fixes'].extend(issue_nums)
            elif line_lower.startswith('related'):
                references['related'].extend(issue_nums)

        return references

    def validate_format(self, commit_message: str) -> Tuple[bool, Optional[str]]:
        """Validate commit message format without parsing.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.parse(commit_message)
            return True, None
        except ValueError as e:
            return False, str(e)
