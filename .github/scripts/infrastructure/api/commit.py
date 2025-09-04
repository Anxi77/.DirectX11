"""Commit operations mixin."""
from typing import Dict, Any, List, Optional
from gql import gql

class CommitMixin:
    """Mixin for commit-related operations."""

    def get_commits(self, repo_owner: str, repo_name: str, since: Optional[str] = None,
                   until: Optional[str] = None, branch: str = "main", first: int = 100) -> List[Dict[str, Any]]:
        """Get repository commits.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            since: Only commits after this date (ISO format)
            until: Only commits before this date (ISO format)
            branch: Branch name to query
            first: Maximum number of commits to fetch

        Returns:
            List of commit data dictionaries
        """
        query = gql("""
            query GetCommits($owner: String!, $name: String!, $ref: String!, $since: GitTimestamp, $until: GitTimestamp, $first: Int!) {
              repository(owner: $owner, name: $name) {
                ref(qualifiedName: $ref) {
                  target {
                    ... on Commit {
                      history(since: $since, until: $until, first: $first) {
                        nodes {
                          oid
                          message
                          committedDate
                          author {
                            name
                            email
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
        """)

        variables = {
            "owner": repo_owner,
            "name": repo_name,
            "ref": f"refs/heads/{branch}",
            "first": first
        }

        if since:
            variables["since"] = since
        if until:
            variables["until"] = until

        result = self._execute_with_retry(query, variables)
        history = result.get('repository', {}).get('ref', {}).get('target', {}).get('history', {})
        return history.get('nodes', []) if history else []

    def get_commit(self, repo_owner: str, repo_name: str, commit_sha: str) -> Dict[str, Any]:
        """Get a single commit by SHA.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            commit_sha: Commit SHA

        Returns:
            Commit data dictionary
        """
        query = gql("""
            query GetCommit($owner: String!, $name: String!, $oid: GitObjectID!) {
              repository(owner: $owner, name: $name) {
                object(oid: $oid) {
                  ... on Commit {
                    oid
                    message
                    committedDate
                    author {
                      name
                      email
                    }
                  }
                }
              }
            }
        """)

        variables = {
            "owner": repo_owner,
            "name": repo_name,
            "oid": commit_sha
        }

        result = self._execute_with_retry(query, variables)
        return result.get('repository', {}).get('object', {}) if result else {}
