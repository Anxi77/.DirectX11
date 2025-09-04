"""Issue operations mixin."""
from typing import Dict, Any, List, Optional
from gql import gql

class IssueMixin:
    """Mixin for issue-related operations."""

    def get_issues(self, repo_owner: str, repo_name: str, state: str = 'OPEN',
                  labels: Optional[List[str]] = None, first: int = 100) -> List[Dict[str, Any]]:
        """Get repository issues.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            state: Issue state ('OPEN', 'CLOSED')
            labels: List of label names to filter by
            first: Maximum number of issues to fetch

        Returns:
            List of issue data dictionaries
        """
        query = gql("""
            query GetIssues($owner: String!, $name: String!, $states: [IssueState!], $labels: [String!], $first: Int!) {
              repository(owner: $owner, name: $name) {
                issues(states: $states, labels: $labels, first: $first, orderBy: {field: CREATED_AT, direction: DESC}) {
                  nodes {
                    id
                    number
                    title
                    body
                    state
                    labels(first: 10) {
                      nodes {
                        name
                      }
                    }
                    assignees(first: 5) {
                      nodes {
                        login
                      }
                    }
                    createdAt
                    updatedAt
                  }
                }
              }
            }
        """)

        variables = {
            "owner": repo_owner,
            "name": repo_name,
            "states": [state],
            "labels": labels or [],
            "first": first
        }

        result = self._execute_with_retry(query, variables)
        return result.get('repository', {}).get('issues', {}).get('nodes', []) if result else []

    def create_issue(self, repo_id: str, title: str, body: str = '',
                    labels: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Create new issue.

        Args:
            repo_id: Repository node ID
            title: Issue title
            body: Issue body content
            labels: List of label IDs

        Returns:
            Created issue data dictionary
        """
        mutation = gql("""
            mutation CreateIssue($repositoryId: ID!, $title: String!, $body: String, $labelIds: [ID!]) {
              createIssue(input: {
                repositoryId: $repositoryId
                title: $title
                body: $body
                labelIds: $labelIds
              }) {
                issue {
                  id
                  number
                  title
                  url
                }
              }
            }
        """)

        variables = {
            "repositoryId": repo_id,
            "title": title,
            "body": body,
            "labelIds": labels or []
        }

        result = self._execute_with_retry(mutation, variables)
        return result.get('createIssue', {}).get('issue') if result else None

    def update_issue(self, issue_id: str, title: Optional[str] = None,
                    body: Optional[str] = None, state: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update existing issue.

        Args:
            issue_id: Issue node ID
            title: New title (optional)
            body: New body content (optional)
            state: New state ('OPEN' or 'CLOSED')

        Returns:
            Updated issue data dictionary
        """
        mutation = gql("""
            mutation UpdateIssue($issueId: ID!, $title: String, $body: String, $state: IssueState) {
              updateIssue(input: {
                id: $issueId
                title: $title
                body: $body
                state: $state
              }) {
                issue {
                  id
                  number
                  title
                  state
                }
              }
            }
        """)

        variables = {"issueId": issue_id}
        if title is not None:
            variables["title"] = title
        if body is not None:
            variables["body"] = body
        if state is not None:
            variables["state"] = state.upper()

        result = self._execute_with_retry(mutation, variables)
        return result.get('updateIssue', {}).get('issue') if result else None

    def create_issue_with_assignees(self, repository_id: str, title: str, body: str = '',
                                   labels: Optional[List[str]] = None,
                                   assignees: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Create new issue with assignees support.

        Args:
            repository_id: Repository node ID
            title: Issue title
            body: Issue body content
            labels: List of label IDs
            assignees: List of GitHub usernames to assign

        Returns:
            Created issue data dictionary
        """
        mutation = gql("""
            mutation CreateIssue($repositoryId: ID!, $title: String!, $body: String, $labelIds: [ID!], $assigneeIds: [ID!]) {
              createIssue(input: {
                repositoryId: $repositoryId
                title: $title
                body: $body
                labelIds: $labelIds
                assigneeIds: $assigneeIds
              }) {
                issue {
                  id
                  number
                  title
                  body
                  url
                  state
                  assignees(first: 10) {
                    nodes {
                      login
                    }
                  }
                }
              }
            }
        """)

        variables = {
            "repositoryId": repository_id,
            "title": title,
            "body": body
        }

        if labels:
            variables["labelIds"] = labels

        if assignees:
            # Convert usernames to user IDs
            assignee_ids = []
            for username in assignees:
                user_id = self.get_user_id(username)
                if user_id:
                    assignee_ids.append(user_id)
            variables["assigneeIds"] = assignee_ids

        result = self._execute_with_retry(mutation, variables)
        return result.get('createIssue', {}).get('issue') if result else None

    def get_issue_by_id(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Get issue by its node ID.

        Args:
            issue_id: Issue node ID

        Returns:
            Issue data dictionary or None if not found
        """
        query = gql("""
            query GetIssue($issueId: ID!) {
              node(id: $issueId) {
                ... on Issue {
                  id
                  number
                  title
                  body
                  state
                  url
                  createdAt
                  updatedAt
                  repository {
                    owner {
                      login
                    }
                    name
                  }
                  assignees(first: 10) {
                    nodes {
                      login
                    }
                  }
                  labels(first: 20) {
                    nodes {
                      name
                      color
                    }
                  }
                }
              }
            }
        """)

        variables = {"issueId": issue_id}
        result = self._execute_with_retry(query, variables)

        return result.get('node') if result else None

    def get_issue(self, repo_owner: str, repo_name: str, issue_number: int) -> Optional[Dict[str, Any]]:
        """Get issue by repository and issue number.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            issue_number: Issue number

        Returns:
            Issue data dictionary or None if not found
        """
        query = gql("""
            query GetIssue($owner: String!, $name: String!, $number: Int!) {
              repository(owner: $owner, name: $name) {
                issue(number: $number) {
                  id
                  number
                  title
                  body
                  state
                  url
                  createdAt
                  updatedAt
                  assignees(first: 10) {
                    nodes {
                      login
                    }
                  }
                  labels(first: 20) {
                    nodes {
                      name
                      color
                    }
                  }
                }
              }
            }
        """)

        variables = {
            "owner": repo_owner,
            "name": repo_name,
            "number": issue_number
        }

        result = self._execute_with_retry(query, variables)
        repository = result.get('repository') if result else None
        return repository.get('issue') if repository else None

    def add_labels_to_issue(self, issue_id: str, label_ids: List[str]) -> Dict[str, Any]:
        """Add labels to an issue.

        Args:
            issue_id: Issue node ID
            label_ids: List of label node IDs to add

        Returns:
            Mutation result
        """
        mutation = gql("""
            mutation AddLabelsToIssue($issueId: ID!, $labelIds: [ID!]!) {
              addLabelsToLabelable(input: {
                labelableId: $issueId
                labelIds: $labelIds
              }) {
                labelable {
                  ... on Issue {
                    id
                    labels(first: 10) {
                      nodes {
                        name
                      }
                    }
                  }
                }
              }
            }
        """)

        variables = {
            "issueId": issue_id,
            "labelIds": label_ids
        }

        return self._execute_with_retry(mutation, variables)

    def remove_labels_from_issue(self, issue_id: str, label_ids: List[str]) -> Dict[str, Any]:
        """Remove labels from an issue.

        Args:
            issue_id: Issue node ID
            label_ids: List of label node IDs to remove

        Returns:
            Mutation result
        """
        mutation = gql("""
            mutation RemoveLabelsFromIssue($issueId: ID!, $labelIds: [ID!]!) {
              removeLabelsFromLabelable(input: {
                labelableId: $issueId
                labelIds: $labelIds
              }) {
                labelable {
                  ... on Issue {
                    id
                    labels(first: 10) {
                      nodes {
                        name
                      }
                    }
                  }
                }
              }
            }
        """)

        variables = {
            "issueId": issue_id,
            "labelIds": label_ids
        }

        return self._execute_with_retry(mutation, variables)
