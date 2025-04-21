"""커밋 이벤트 핸들러"""
from typing import Dict
from .base import BaseHandler
from ..formatters.commit import CommitFormatter
from config.user_mappings import get_slack_users_by_position
class CommitHandler(BaseHandler):
    """커밋 이벤트 처리"""
    
    def handle(self, event_data: Dict):
        """커밋 이벤트 처리"""
        repository = event_data['repository']['full_name']
        branch = event_data['ref'].split('/')[-1]
        commits = event_data['commits']
        user_id = get_slack_users_by_position('head_developer')[0]
        if commits:
            message = CommitFormatter.format_commits(commits, repository, branch)

            blocks = message['blocks']
            text = message['blocks'][0]['text']['text']
            
            self.client.send_dm(user_id,blocks,text); 