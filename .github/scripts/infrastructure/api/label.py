"""Label operations mixin."""
from typing import Optional, Dict, Any
from gql import gql

class LabelMixin:
    """Mixin for label-related operations."""

    def get_label_id_by_name(self, repo_owner: str, repo_name: str, label_name: str) -> Optional[str]:
        """Get label ID by name.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            label_name: Label name to find

        Returns:
            Label ID or None if not found
        """
        labels = self.get_repository_labels(repo_owner, repo_name)
        self.logger.debug(f"Found {len(labels)} labels in {repo_owner}/{repo_name}")
        
        for label in labels:
            label_name_found = label.get('name')
            if label_name_found == label_name:
                label_id = label.get('id')
                self.logger.debug(f"Found label '{label_name}' with ID: {label_id}")
                return label_id
            self.logger.debug(f"Label '{label_name_found}' does not match '{label_name}'")
        
        self.logger.debug(f"Label '{label_name}' not found among existing labels")
        return None

    def create_label(self, repo_id: str, name: str, color: str = "0969da", description: str = "") -> Optional[Dict[str, Any]]:
        """Create a new label in the repository.

        Args:
            repo_id: Repository ID
            name: Label name
            color: Label color (hex without #)
            description: Label description

        Returns:
            Created label data or None if failed
        """
        mutation = gql("""
            mutation CreateLabel($repositoryId: ID!, $name: String!, $color: String!, $description: String) {
                createLabel(input: {
                    repositoryId: $repositoryId
                    name: $name
                    color: $color
                    description: $description
                }) {
                    label {
                        id
                        name
                        color
                        description
                        url
                    }
                }
            }
        """)

        variables = {
            "repositoryId": repo_id,
            "name": name,
            "color": color,
            "description": description
        }

        try:
            result = self._execute_with_retry(mutation, variables)
            return result.get('createLabel', {}).get('label') if result else None
        except Exception as e:
            # Check if it's a "name already taken" error
            error_msg = str(e).lower()
            if 'name has already been taken' in error_msg or 'already been taken' in error_msg:
                self.logger.warning(f"Label '{name}' already exists (created by another process)")
                return None  # Let get_or_create_label handle the retry
            else:
                self.logger.error(f"Failed to create label '{name}': {e}")
                return None

    def get_or_create_label(self, repo_owner: str, repo_name: str, label_name: str, color: str = "0969da", description: str = "") -> Optional[str]:
        """Get label ID by name, create if it doesn't exist.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            label_name: Label name
            color: Label color (hex without #) for creation
            description: Label description for creation

        Returns:
            Label ID or None if failed
        """
        # First try to get existing label
        label_id = self.get_label_id_by_name(repo_owner, repo_name, label_name)
        if label_id:
            return label_id

        # Get repository ID for label creation
        repo = self.get_repository(repo_owner, repo_name)
        if not repo:
            self.logger.error(f"Repository {repo_owner}/{repo_name} not found")
            return None

        repo_id = repo.get('id')
        if not repo_id:
            self.logger.error(f"Could not get repository ID for {repo_owner}/{repo_name}")
            return None

        # Create the label
        self.logger.info(f"Creating label '{label_name}' in {repo_owner}/{repo_name}")
        created_label = self.create_label(repo_id, label_name, color, description)

        if created_label:
            self.logger.info(f"Successfully created label '{label_name}' with ID: {created_label.get('id')}")
            return created_label.get('id')
        else:
            # If creation failed, try to get the label again (might have been created by another process)
            self.logger.warning(f"Failed to create label '{label_name}', checking if it exists now...")
            label_id = self.get_label_id_by_name(repo_owner, repo_name, label_name)
            if label_id:
                self.logger.info(f"Label '{label_name}' found after creation failure (created by another process?)")
                return label_id
            else:
                self.logger.error(f"Failed to create or find label '{label_name}'")
                return None
