"""
GitHub API 클라이언트
"""
import os
import logging
import requests
from github import Github
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token: str, org: str = None):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.g = Github(token)
        
        repo_name = os.environ.get('GITHUB_REPOSITORY', '')
        if '/' in repo_name:
            self.org = repo_name.split('/')[0]
        else:
            self.org = org or 'KGAMeta8thTeam1'
        
        logger.info(f"조직 설정: {self.org}")

    def _execute_graphql(self, query: str, variables: Dict[str, Any]) -> Optional[Dict]:
        """GraphQL 쿼리를 실행합니다."""
        try:
            response = requests.post(
                'https://api.github.com/graphql',
                json={'query': query, 'variables': variables},
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            
            if 'errors' in result:
                logger.error(f"GraphQL 오류: {result['errors']}")
                return None
            
            return result['data']
        except Exception as e:
            logger.error(f"GraphQL 쿼리 실행 중 오류 발생: {str(e)}")
            return None

    def get_repo(self) -> Any:
        """현재 리포지토리 객체를 반환합니다."""
        return self.g.get_repo(os.environ.get('GITHUB_REPOSITORY')) 