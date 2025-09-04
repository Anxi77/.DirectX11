"""Enhanced API client with modular GraphQL implementation."""

# Import data models for backward compatibility
from .models import FieldInfo, BoardItem

# Import all mixins
from .api import (
    BaseAPIClient,
    RepositoryMixin,
    IssueMixin,
    LabelMixin,
    ProjectMixin,
    CommitMixin,
    UserMixin
)

class APIClient(
    BaseAPIClient,
    RepositoryMixin,
    IssueMixin,
    LabelMixin,
    ProjectMixin,
    CommitMixin,
    UserMixin
):
    """GraphQL API client with modular architecture.

    Combines all domain-specific mixins to provide the same interface
    as the original monolithic implementation while maintaining better
    code organization and maintainability.
    """

    def __init__(self, token: str, max_retries: int = 3, base_delay: float = 1.0):
        """Initialize API client with all mixins.

        Args:
            token: Personal access token
            max_retries: Maximum retry attempts for rate limiting
            base_delay: Base delay for exponential backoff
        """
        # Initialize the base client which sets up GraphQL connection
        super().__init__(token, max_retries, base_delay)

# Export data models for backward compatibility
__all__ = ['APIClient', 'FieldInfo', 'BoardItem']
