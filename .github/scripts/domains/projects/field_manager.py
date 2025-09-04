"""Project field and category management utilities."""
import logging
from typing import Optional

class ProjectFieldManager:
    """Manages GitHub project fields and categories."""

    def __init__(self, api_client, project_id: str, project_owner: str):
        """Initialize project field manager.

        Args:
            api_client: GitHub API client
            project_id: GitHub project ID
            project_owner: Project owner
        """
        self.api = api_client
        self.project_id = project_id
        self.project_owner = project_owner
        self.logger = logging.getLogger(__name__)
        self._category_field_id: Optional[str] = None

    def ensure_category_field_exists(self, category_name: str) -> bool:
        """Ensure category field exists and contains the specified category.

        Args:
            category_name: Name of the category to ensure exists

        Returns:
            True if category field exists and contains the category
        """
        try:
            # Get or create category field
            field_id = self._get_or_create_category_field()
            if not field_id:
                return False

            # Ensure the specific category option exists
            self._ensure_category_option_exists(field_id, category_name)
            return True

        except Exception as e:
            self.logger.error(f"Failed to ensure category field exists: {e}")
            return False

    def _get_or_create_category_field(self) -> Optional[str]:
        """Get existing category field or create new one.

        Returns:
            Field ID if successful, None otherwise
        """
        if self._category_field_id:
            return self._category_field_id

        try:
            # Get project fields
            project_fields = self.api.get_project_fields(self.project_id)

            # Look for existing category field
            for field in project_fields:
                if field.get('name', '').lower() == 'category':
                    self._category_field_id = field.get('id')
                    return self._category_field_id

            # Create category field if it doesn't exist
            self._category_field_id = self._create_category_field()
            return self._category_field_id

        except Exception as e:
            self.logger.error(f"Failed to get or create category field: {e}")
            return None

    def _create_category_field(self) -> Optional[str]:
        """Create a new category field for the project.

        Returns:
            Field ID if successful, None otherwise
        """
        try:
            field_info = self.api.create_project_field(
                project_id=self.project_id,
                field_name="Category",
                field_type="SINGLE_SELECT",
                options=[]  # Will be populated as categories are added
            )

            if field_info:
                self.logger.info("Created category field for project")
                return field_info.get('id')

        except Exception as e:
            self.logger.error(f"Failed to create category field: {e}")

        return None

    def _ensure_category_option_exists(self, field_id: str, category_name: str):
        """Ensure a category option exists in the category field.

        Args:
            field_id: Category field ID
            category_name: Name of the category option to ensure exists
        """
        try:
            # Get current field options
            field_info = self.api.get_project_field_info(self.project_id, field_id)
            if not field_info:
                return

            # Check if option already exists
            options = field_info.get('options', [])
            for option in options:
                if option.get('name') == category_name:
                    return  # Option already exists

            # Add new category option
            self.api.add_project_field_option(
                project_id=self.project_id,
                field_id=field_id,
                option_name=category_name,
                option_color="d4c5f9"  # Light purple default color
            )

            self.logger.debug(f"Added category option '{category_name}' to field")

        except Exception as e:
            self.logger.error(f"Failed to ensure category option exists: {e}")
