"""Repository operations mixin."""
from typing import Dict, Any, Optional
from gql import gql

class RepositoryMixin:
    """Mixin for repository-related operations."""

    def get_repository(self, owner: str, repo_name: str) -> Optional[Dict[str, Any]]:
        """Get repository information.

        Args:
            owner: Repository owner
            repo_name: Repository name

        Returns:
            Repository data dictionary
        """
        query = gql("""
            query GetRepository($owner: String!, $name: String!) {
              repository(owner: $owner, name: $name) {
                id
                name
                nameWithOwner
                isPrivate
                url
              }
            }
        """)

        variables = {"owner": owner, "name": repo_name}
        result = self._execute_with_retry(query, variables)
        return result.get('repository') if result else None

    def get_repository_labels(self, repo_owner: str, repo_name: str) -> list:
        """Get all repository labels.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name

        Returns:
            List of label dictionaries with id, name, color
        """
        query = gql("""
            query GetLabels($owner: String!, $name: String!) {
              repository(owner: $owner, name: $name) {
                labels(first: 100) {
                  nodes {
                    id
                    name
                    color
                    description
                  }
                }
              }
            }
        """)

        variables = {"owner": repo_owner, "name": repo_name}
        result = self._execute_with_retry(query, variables)
        return result.get('repository', {}).get('labels', {}).get('nodes', []) if result else []
