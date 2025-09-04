"""Project and board operations mixin."""
from typing import Dict, Any, List, Optional, Union
from gql import gql
import time

class ProjectMixin:
    """Mixin for project and board-related operations."""

    def get_board_with_items(self, owner: str, board_number: int,
                            first: int = 100) -> Dict[str, Any]:
        """Get board with all items and issues in single query.

        Args:
            owner: Organization/user login
            board_number: Board number
            first: Maximum items to fetch

        Returns:
            Complete board data with items and content
        """
        query = gql("""
            query GetBoard($owner: String!, $number: Int!, $first: Int!) {
              organization(login: $owner) {
                projectV2(number: $number) {
                  id
                  title
                  url
                  fields(first: 20) {
                    nodes {
                      ... on ProjectV2Field {
                        id
                        name
                        dataType
                      }
                      ... on ProjectV2SingleSelectField {
                        id
                        name
                        dataType
                        options {
                          id
                          name
                        }
                      }
                    }
                  }
                  items(first: $first) {
                    nodes {
                      id
                      content {
                        ... on Issue {
                          id
                          number
                          title
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
                        }
                      }
                      fieldValues(first: 10) {
                        nodes {
                          ... on ProjectV2ItemFieldTextValue {
                            field {
                              ... on ProjectV2Field {
                                name
                              }
                            }
                            text
                          }
                          ... on ProjectV2ItemFieldSingleSelectValue {
                            field {
                              ... on ProjectV2SingleSelectField {
                                name
                              }
                            }
                            optionId
                            name
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
            "owner": owner,
            "number": board_number,
            "first": first
        }

        result = self._execute_with_retry(query, variables)

        # Cache field information
        if result and 'organization' in result and result['organization']:
            board_data = result['organization']['projectV2']
            if board_data:
                self._cache_fields(f"{owner}:{board_number}", board_data['fields']['nodes'])

        return result

    def add_item_to_board(self, board_id: str, content_id: str) -> Dict[str, Any]:
        """Add issue to board.

        Args:
            board_id: Board ID
            content_id: Issue node ID

        Returns:
            Mutation result
        """
        mutation = gql("""
            mutation AddItem($boardId: ID!, $contentId: ID!) {
              addProjectV2ItemById(input: {
                projectId: $boardId
                contentId: $contentId
              }) {
                item {
                  id
                  content {
                    ... on Issue {
                      number
                      title
                    }
                  }
                }
              }
            }
        """)

        variables = {
            "boardId": board_id,
            "contentId": content_id
        }

        return self._execute_with_retry(mutation, variables)

    def update_item_field(self, board_id: str, item_id: str,
                         field_id: str, value: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Update board item field value.

        Args:
            board_id: Board ID
            item_id: Item ID
            field_id: Field ID to update
            value: New field value (text or single select option)

        Returns:
            Mutation result
        """
        # Handle different field value types
        if isinstance(value, dict) and 'singleSelectOptionId' in value:
            # Single select field
            mutation = gql("""
                mutation UpdateField($boardId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
                  updateProjectV2ItemFieldValue(input: {
                    projectId: $boardId
                    itemId: $itemId
                    fieldId: $fieldId
                    value: $value
                  }) {
                    projectV2Item {
                      id
                    }
                  }
                }
            """)

            field_value = {
                "singleSelectOptionId": value['singleSelectOptionId']
            }
        else:
            # Text field
            mutation = gql("""
                mutation UpdateField($boardId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
                  updateProjectV2ItemFieldValue(input: {
                    projectId: $boardId
                    itemId: $itemId
                    fieldId: $fieldId
                    value: $value
                  }) {
                    projectV2Item {
                      id
                    }
                  }
                }
            """)

            field_value = {
                "text": str(value)
            }

        variables = {
            "boardId": board_id,
            "itemId": item_id,
            "fieldId": field_id,
            "value": field_value
        }

        return self._execute_with_retry(mutation, variables)

    def batch_update_items(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch update multiple board items efficiently.

        Args:
            updates: List of update operations with keys:
                    - board_id, item_id, field_id, value

        Returns:
            List of mutation results
        """
        results = []

        # Group updates by board for efficiency
        board_groups = {}
        for update in updates:
            board_id = update['board_id']
            if board_id not in board_groups:
                board_groups[board_id] = []
            board_groups[board_id].append(update)

        # Execute updates in batches
        for board_id, board_updates in board_groups.items():
            for update in board_updates:
                result = self.update_item_field(
                    update['board_id'],
                    update['item_id'],
                    update['field_id'],
                    update['value']
                )
                results.append(result)

                # Small delay between mutations to avoid rate limiting
                time.sleep(0.1)

        return results

    def get_field_id_by_name(self, owner: str, board_number: int, field_name: str) -> Optional[str]:
        """Get field ID by name using cached field information.

        Args:
            owner: Organization/user login
            board_number: Board number
            field_name: Field name to find

        Returns:
            Field ID or None if not found
        """
        board_key = f"{owner}:{board_number}"

        # Load fields if not cached
        if board_key not in self._field_cache:
            board_data = self.get_board_with_items(owner, board_number, first=1)
            if not board_data or not board_data.get('organization', {}).get('projectV2'):
                return None

        # Search cached fields
        fields_cache = self._field_cache.get(board_key, {})
        field_info = fields_cache.get(field_name)
        return field_info.field_id if field_info else None

    def get_select_option_id(self, owner: str, board_number: int,
                           field_name: str, option_name: str) -> Optional[str]:
        """Get single select option ID for field value updates.

        Args:
            owner: Organization/user login
            board_number: Board number
            field_name: Field name
            option_name: Option name to find

        Returns:
            Option ID or None if not found
        """
        board_key = f"{owner}:{board_number}"
        fields_cache = self._field_cache.get(board_key, {})
        field_info = fields_cache.get(field_name)

        if not field_info or not field_info.options:
            return None

        for option in field_info.options:
            if option['name'] == option_name:
                return option['id']

        return None

    def get_board_items(self, board_data: Dict[str, Any]) -> list:
        """Parse board items from board data.

        Args:
            board_data: Board data dictionary from API

        Returns:
            List of BoardItem objects
        """
        from ..models.board import BoardItem

        if not isinstance(board_data, dict) or 'items' not in board_data:
            return []

        items_data = board_data['items']['nodes']
        board_items = []

        for item_data in items_data:
            # Parse field values
            field_values = {}
            for field_value in item_data.get('fieldValues', {}).get('nodes', []):
                if 'field' in field_value and 'name' in field_value['field']:
                    field_name = field_value['field']['name']
                    if 'text' in field_value:
                        field_values[field_name] = field_value['text']
                    elif 'name' in field_value:  # Single select
                        field_values[field_name] = field_value['name']

            # Extract content info
            content = item_data.get('content', {})
            board_item = BoardItem(
                item_id=item_data['id'],
                content_id=content.get('id'),
                content_type='Issue' if 'number' in content else None,
                content_number=content.get('number'),
                content_title=content.get('title'),
                field_values=field_values
            )

            board_items.append(board_item)

        return board_items

    def list_organization_projects(self, owner: str, first: int = 20) -> List[Dict[str, Any]]:
        """List organization projects.

        Args:
            owner: Organization login
            first: Maximum number of projects to fetch

        Returns:
            List of project dictionaries with id, number, title
        """
        query = gql("""
            query ListOrganizationProjects($owner: String!, $first: Int!) {
              organization(login: $owner) {
                projectsV2(first: $first, orderBy: {field: CREATED_AT, direction: DESC}) {
                  nodes {
                    id
                    number
                    title
                    url
                    createdAt
                    updatedAt
                  }
                }
              }
            }
        """)

        variables = {"owner": owner, "first": first}
        result = self._execute_with_retry(query, variables)
        return result.get('organization', {}).get('projectsV2', {}).get('nodes', []) if result else []

    def list_user_projects(self, owner: str, first: int = 20) -> List[Dict[str, Any]]:
        """List user projects.

        Args:
            owner: User login
            first: Maximum number of projects to fetch

        Returns:
            List of project dictionaries with id, number, title
        """
        query = gql("""
            query ListUserProjects($owner: String!, $first: Int!) {
              user(login: $owner) {
                projectsV2(first: $first, orderBy: {field: CREATED_AT, direction: DESC}) {
                  nodes {
                    id
                    number
                    title
                    url
                    createdAt
                    updatedAt
                  }
                }
              }
            }
        """)

        variables = {"owner": owner, "first": first}
        result = self._execute_with_retry(query, variables)
        return result.get('user', {}).get('projectsV2', {}).get('nodes', []) if result else []

    def create_user_project(self, owner: str, title: str,
                          description: str = '') -> Optional[Dict[str, Any]]:
        """Create new user project.

        Args:
            owner: User login
            title: Project title
            description: Project description

        Returns:
            Created project data dictionary
        """
        # First get user ID
        user_query = gql("""
            query GetUser($login: String!) {
              user(login: $login) {
                id
              }
            }
        """)

        user_result = self._execute_with_retry(user_query, {"login": owner})
        if not user_result:
            return None

        user_id = user_result.get('user', {}).get('id')
        if not user_id:
            return None

        # Create project
        mutation = gql("""
            mutation CreateProjectV2($ownerId: ID!, $title: String!) {
              createProjectV2(input: {
                ownerId: $ownerId
                title: $title
              }) {
                projectV2 {
                  id
                  number
                  title
                  url
                }
              }
            }
        """)

        variables = {
            "ownerId": user_id,
            "title": title
        }

        result = self._execute_with_retry(mutation, variables)
        
        if not result:
            self.logger.error(f"No result returned from user project creation mutation for {owner}")
            return None
            
        if 'errors' in result:
            self.logger.error(f"GraphQL errors in user project creation: {result['errors']}")
            return None
            
        create_result = result.get('createProjectV2', {})
        project = create_result.get('projectV2')
        if not project:
            self.logger.error(f"No project data in createProjectV2 result: {create_result}")
            return None
            
        return project

    def create_organization_project(self, owner: str, title: str,
                                  description: str = '') -> Optional[Dict[str, Any]]:
        """Create new organization project.

        Args:
            owner: Organization login
            title: Project title
            description: Project description

        Returns:
            Created project data dictionary
        """
        # First get organization ID
        org_query = gql("""
            query GetOrganization($login: String!) {
              organization(login: $login) {
                id
              }
            }
        """)

        org_result = self._execute_with_retry(org_query, {"login": owner})
        if not org_result:
            return None

        org_id = org_result.get('organization', {}).get('id')
        if not org_id:
            return None

        # Create project
        mutation = gql("""
            mutation CreateProjectV2($ownerId: ID!, $title: String!) {
              createProjectV2(input: {
                ownerId: $ownerId
                title: $title
              }) {
                projectV2 {
                  id
                  number
                  title
                  url
                  createdAt
                }
              }
            }
        """)

        variables = {
            "ownerId": org_id,
            "title": title
        }

        result = self._execute_with_retry(mutation, variables)
        return result.get('createProjectV2', {}).get('projectV2') if result else None

    def get_project_by_name(self, owner: str, project_name: str) -> Optional[Dict[str, Any]]:
        """Get project by exact name match, supporting both users and organizations.

        Args:
            owner: User or organization login
            project_name: Exact project name to find

        Returns:
            Project data dictionary or None if not found
        """
        # Try user projects first
        try:
            user_projects = self.list_user_projects(owner)
            self.logger.info(f"Found {len(user_projects)} user projects for {owner}")
            for project in user_projects:
                project_title = project.get('title', '')
                project_number = project.get('number', 'unknown')
                self.logger.info(f"  Project #{project_number}: '{project_title}'")
                if project_title == project_name:
                    return project
        except Exception as e:
            self.logger.warning(f"Failed to list user projects: {e}")
            # If user query fails, try organization
            pass

        # Try organization projects
        try:
            org_projects = self.list_organization_projects(owner)
            for project in org_projects:
                if project.get('title') == project_name:
                    return project
        except Exception:
            # If both fail, return None
            pass

        return None

    def get_or_create_project_by_name(self, owner: str, project_name: str) -> Optional[Dict[str, Any]]:
        """Find existing project by name only (no creation attempts).

        Args:
            owner: User or organization login
            project_name: Project name to find

        Returns:
            Project data dictionary or None if not found
        """
        # Only try to find existing project - no creation attempts
        existing_project = self.get_project_by_name(owner, project_name)
        if existing_project:
            self.logger.info(f"Found existing project '{project_name}' (#{existing_project['number']})")
            return existing_project

        # Project not found - provide guidance
        self.logger.warning(f"Project '{project_name}' not found for {owner}")
        self.logger.info(f"Please create project '{project_name}' manually in GitHub")
        self.logger.info("The automation system will automatically discover it on next run")
        
        return None

        # Provide detailed error guidance based on token type
        token_type = getattr(self, 'token_type', 'GitHub Token')
        
        self.logger.error(f"Failed to create project '{project_name}' for {owner}")
        
        if hasattr(self, 'is_pat') and not self.is_pat:
            # This is a GitHub Actions token
            self.logger.error("⚠️  GITHUB ACTIONS TOKEN LIMITATION DETECTED")
            self.logger.error("GitHub Actions tokens have limited permissions for Projects v2 operations")
            self.logger.error("SOLUTION: Create a Personal Access Token (PAT) with 'project' scope:")
            self.logger.error("1. Go to https://github.com/settings/tokens/new")
            self.logger.error("2. Check 'project' scope (required for Projects v2)")  
            self.logger.error("3. Add PAT as 'PAT' secret in repository settings")
            self.logger.error("4. The workflow will automatically use PAT instead of GITHUB_TOKEN")
        else:
            # This is a PAT but still failing
            self.logger.error(f"Using {token_type} but project creation still failed")
            self.logger.error("Possible issues:")
            self.logger.error("1. Missing 'project' scope in Personal Access Token")
            self.logger.error("2. User/Organization doesn't have Projects v2 enabled") 
            self.logger.error("3. Token doesn't have permission to create projects for this owner")
            
        return None

    def create_project_field(self, project_id: str, field_name: str, field_type: str = 'SINGLE_SELECT',
                           options: List[str] = None) -> Optional[str]:
        """Create a new field in a project.

        Args:
            project_id: Project ID
            field_name: Name of the field to create
            field_type: Type of field (SINGLE_SELECT, TEXT, NUMBER, DATE, ITERATION)
            options: List of options for single select fields

        Returns:
            Field ID if created successfully, None otherwise
        """
        try:
            if field_type == 'SINGLE_SELECT' and not options:
                options = ['General']  # Default option

            mutation = gql("""
                mutation CreateProjectField($projectId: ID!, $name: String!, $dataType: ProjectV2CustomFieldType!, $options: [ProjectV2SingleSelectFieldOptionInput!]) {
                  createProjectV2Field(input: {
                    projectId: $projectId
                    name: $name
                    dataType: $dataType
                    singleSelectOptions: $options
                  }) {
                    projectV2Field {
                      ... on ProjectV2Field {
                        id
                        name
                      }
                      ... on ProjectV2SingleSelectField {
                        id
                        name
                        options {
                          id
                          name
                        }
                      }
                    }
                  }
                }
            """)

            variables = {
                "projectId": project_id,
                "name": field_name,
                "dataType": field_type
            }

            if field_type == 'SINGLE_SELECT' and options:
                variables["options"] = [
                    {
                        "name": option,
                        "color": "GRAY",  # Default color
                        "description": f"{option} category"  # Default description
                    } 
                    for option in options
                ]

            result = self._execute_with_retry(mutation, variables)

            if result and 'createProjectV2Field' in result:
                field_data = result['createProjectV2Field']['projectV2Field']
                field_id = field_data.get('id')

                if field_id:
                    self.logger.info(f"Created project field '{field_name}' with ID: {field_id}")
                    return field_id

            return None

        except Exception as e:
            self.logger.error(f"Failed to create project field '{field_name}': {e}")
            return None

    def get_project_items(self, project_id: str, first: int = 100) -> List[Dict[str, Any]]:
        """Get project items by project ID.

        Args:
            project_id: Project ID
            first: Maximum items to fetch

        Returns:
            List of project items
        """
        query = gql("""
            query GetProjectItems($projectId: ID!, $first: Int!) {
              node(id: $projectId) {
                ... on ProjectV2 {
                  items(first: $first) {
                    nodes {
                      id
                      content {
                        ... on Issue {
                          id
                          number
                          title
                          state
                          labels(first: 10) {
                            nodes {
                              name
                            }
                          }
                        }
                      }
                      fieldValues(first: 10) {
                        nodes {
                          ... on ProjectV2ItemFieldTextValue {
                            field {
                              ... on ProjectV2Field {
                                name
                              }
                            }
                            text
                          }
                          ... on ProjectV2ItemFieldSingleSelectValue {
                            field {
                              ... on ProjectV2SingleSelectField {
                                name
                              }
                            }
                            optionId
                            name
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
            "projectId": project_id,
            "first": first
        }

        result = self._execute_with_retry(query, variables)
        if result and 'node' in result and result['node']:
            return result['node'].get('items', {}).get('nodes', [])
        return []

    def get_project_fields(self, project_id: str) -> List[Dict[str, Any]]:
        """Get project fields by project ID.

        Args:
            project_id: Project ID

        Returns:
            List of project fields
        """
        query = gql("""
            query GetProjectFields($projectId: ID!) {
              node(id: $projectId) {
                ... on ProjectV2 {
                  fields(first: 20) {
                    nodes {
                      ... on ProjectV2Field {
                        id
                        name
                        dataType
                      }
                      ... on ProjectV2SingleSelectField {
                        id
                        name
                        dataType
                        options {
                          id
                          name
                        }
                      }
                    }
                  }
                }
              }
            }
        """)

        variables = {
            "projectId": project_id
        }

        result = self._execute_with_retry(query, variables)
        if result and 'node' in result and result['node']:
            return result['node'].get('fields', {}).get('nodes', [])
        return []

    def create_project_item(self, project_id: str, content_id: str) -> Dict[str, Any]:
        """Create project item (alias for add_item_to_board).

        Args:
            project_id: Project ID
            content_id: Issue node ID

        Returns:
            Mutation result
        """
        return self.add_item_to_board(project_id, content_id)
