"""Base API client with core GraphQL functionality."""
import time
import logging
from typing import Dict, Any, Optional
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

class BaseAPIClient:
    """Base GraphQL API client with retry logic and core functionality."""

    def __init__(self, token: str, max_retries: int = 3, base_delay: float = 1.0):
        """Initialize base API client.

        Args:
            token: Personal access token or GitHub token
            max_retries: Maximum retry attempts for rate limiting
            base_delay: Base delay for exponential backoff
        """
        self.token = token
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.logger = logging.getLogger(__name__)

        # Check token type for better error messaging
        self.is_pat = token.startswith('ghp_') or token.startswith('github_pat_')
        self.token_type = 'Personal Access Token' if self.is_pat else 'GitHub Actions Token'
        
        self.logger.info(f"Initializing API client with {self.token_type}")

        # Initialize GraphQL transport
        transport = RequestsHTTPTransport(
            url="https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {token}"},
            retries=max_retries
        )

        self.client = Client(transport=transport, fetch_schema_from_transport=True)

        # Cache for field mappings
        self._field_cache: Dict[str, Dict[str, Any]] = {}

    def get_rate_limit(self) -> Dict[str, Any]:
        """Get current rate limit status.

        Returns:
            Dictionary with rate limit information
        """
        query = gql("""
            query GetRateLimit {
              rateLimit {
                limit
                remaining
                resetAt
                used
              }
            }
        """)

        result = self._execute_with_retry(query, {})
        rate_limit = result.get('rateLimit', {}) if result else {}

        return {
            'limit': rate_limit.get('limit', 0),
            'remaining': rate_limit.get('remaining', 0),
            'reset': rate_limit.get('resetAt'),
            'used': rate_limit.get('used', 0)
        }

    def _cache_fields(self, board_key: str, fields_data: list) -> None:
        """Cache board field information for efficient lookups.

        Args:
            board_key: Board identifier key
            fields_data: List of field data dictionaries
        """
        from ..models.field import FieldInfo

        fields_cache = {}

        for field in fields_data:
            field_info = FieldInfo(
                field_id=field['id'],
                name=field['name'],
                data_type=field['dataType'],
                options=field.get('options', []) if 'options' in field else None
            )
            fields_cache[field['name']] = field_info

        self._field_cache[board_key] = fields_cache

    def _execute_with_retry(self, query_or_mutation, variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute operation with retry logic for rate limiting.

        Args:
            query_or_mutation: GraphQL query or mutation
            variables: Variables for the operation

        Returns:
            Operation result or None if failed
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                result = self.client.execute(query_or_mutation, variable_values=variables)
                return result

            except Exception as e:
                last_exception = e
                error_str = str(e).lower()

                # Handle rate limiting
                if 'rate limit' in error_str or 'abuse detection' in error_str:
                    if attempt < self.max_retries:
                        delay = self.base_delay * (2 ** attempt)
                        self.logger.warning(
                            f"Rate limited, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries + 1})"
                        )
                        time.sleep(delay)
                        continue

                # Handle secondary rate limits
                elif 'secondary rate limit' in error_str:
                    if attempt < self.max_retries:
                        delay = 60  # Wait 1 minute
                        self.logger.warning(
                            f"Secondary rate limit, waiting {delay}s"
                        )
                        time.sleep(delay)
                        continue

                # For other errors, don't retry
                raise

        # All retries exhausted
        raise last_exception

    def close(self):
        """Close the API client connection."""
        if hasattr(self.client.transport, 'close'):
            self.client.transport.close()
