"""
태스크 이벤트 핸들러
"""
from typing import Dict
from .base import BaseHandler
from ..formatters.task import TaskFormatter
from config.user_mappings import GITHUB_USER_MAPPING

class TaskHandler(BaseHandler):
    """태스크 이벤트 처리"""
    
    def handle(self, event_data: Dict):
        """태스크 이벤트 처리"""
        task_data = event_data['issue']
        event_type = event_data['action']
        
        # 채널 알림 전송
        message = TaskFormatter.format_task(task_data, event_type)
        self.client.send_channel_notification(message)
        
        # 할당된 경우 담당자에게 DM 전송
        if event_type == 'assigned':
            assignee = event_data['assignee']['login']
            user_info = GITHUB_USER_MAPPING.get(assignee)
            if user_info and user_info.get('slack_id'):
                parent_task = self._get_parent_task_info(task_data)
                
                labels = [label['name'] for label in task_data.get('labels', [])]
                is_todo = any('todo-generated' in label.lower() for label in labels)
                
                header_text = "🎯 새로운 할일이 할당되었습니다"
                if is_todo:
                    header_text = "📝 새로운 Todo가 할당되었습니다"
                
                blocks = [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": header_text}
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*할일:*\n{task_data['title']}"},
                            {"type": "mrkdwn", "text": f"*상태:*\n{task_data['state']}"}
                        ]
                    }
                ]
                
                if parent_task:
                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*상위 태스크:*\n<{parent_task['url']}|{parent_task['title']}>"}
                    })
                
                blocks.extend([
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"👉 <{task_data['html_url']}|할일 보러가기>"}
                    },
                    {"type": "divider"}
                ])
                
                message_text = f"새로운 할일이 할당되었습니다: {task_data['title']}"
                if is_todo:
                    message_text = f"새로운 Todo가 할당되었습니다: {task_data['title']}"
                
                try:
                    # DM 전송 시도
                    self.client.send_dm(
                        user_info['slack_id'],
                        blocks,
                        message_text
                    )
                except Exception as e:
                    print(f"DM 전송 실패, 채널에 멘션으로 대체합니다: {str(e)}")
                    # DM 전송 실패 시 채널에 멘션으로 대체
                    self._send_mention_to_channel(user_info, task_data, is_todo)
    
    def _send_mention_to_channel(self, user_info: Dict, task_data: Dict, is_todo: bool):
        """채널에 멘션 전송"""
        slack_id = user_info['slack_id']
        user_name = user_info['name']
        
        # Slack ID에서 '@' 제거
        if slack_id.startswith('@'):
            slack_id = slack_id[1:]
        
        header_text = "🎯 새로운 할일이 할당되었습니다"
        if is_todo:
            header_text = "📝 새로운 Todo가 할당되었습니다"
        
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{header_text}*\n<@{slack_id}> 님에게 새로운 할일이 할당되었습니다."}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*할일:*\n{task_data['title']}"},
                    {"type": "mrkdwn", "text": f"*상태:*\n{task_data['state']}"}
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"👉 <{task_data['html_url']}|할일 보러가기>"}
            },
            {"type": "divider"}
        ]
        
        message = {
            "blocks": blocks,
            "text": f"{user_name}님에게 새로운 할일이 할당되었습니다: {task_data['title']}"
        }
        
        self.client.send_channel_notification(message)
    
    def _get_parent_task_info(self, task_data: Dict) -> Dict:
        """할일의 상위 태스크 정보를 추출"""
        body = task_data.get('body', '')
        if not body:
            return None
            
        # 본문에서 상위 태스크 링크 찾기
        lines = body.split('\n')
        for line in lines:
            if '상위 태스크:' in line or '관련 태스크:' in line:
                # GitHub 이슈 링크 형식: [...](URL) 또는 <URL>
                import re
                url_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)|<([^>]+)>', line)
                if url_match:
                    url = url_match.group(2) or url_match.group(3)
                    title = url_match.group(1) if url_match.group(2) else url
                    return {'url': url, 'title': title}
        
        return None 