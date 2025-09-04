"""User operations mixin."""
from typing import Optional
from gql import gql

class UserMixin:
    """Mixin for user-related operations."""

    def get_user_id(self, username: str) -> Optional[str]:
        """Get user ID from username.

        Args:
            username: GitHub username

        Returns:
            User node ID or None if not found
        """
        query = gql("""
            query GetUser($login: String!) {
              user(login: $login) {
                id
                login
              }
            }
        """)

        variables = {"login": username}
        result = self._execute_with_retry(query, variables)

        user = result.get('user') if result else None
        return user.get('id') if user else None
