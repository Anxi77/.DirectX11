"""
태스크 메시지 포맷터
"""
from typing import Dict, List
from .base import BaseFormatter

class TaskFormatter(BaseFormatter):
    """태스크 관련 메시지 포맷팅"""
    
    @classmethod
    def format_task(cls, task: Dict, event_type: str) -> Dict:
        """태스크 메시지 포맷팅"""
        title = task['title']
        url = task['html_url']
        user = task['user']['login']
        labels = [label['name'] for label in task.get('labels', [])]
        
        category = next((label.replace('category:', '') for label in labels if label.startswith('category:')), "미분류")
        weight = next((label.replace('weight:', '') for label in labels if label.startswith('weight:')), "미정")
        
        header_text = {
            'opened': "🎯 새로운 태스크가 생성되었습니다",
            'closed': "✅ 태스크가 완료되었습니다",
        }.get(event_type, "ℹ️ 태스크가 업데이트되었습니다")
        
        return {
            "blocks": [
                cls.create_header(header_text),
                cls.create_section(fields=[
                    {"type": "mrkdwn", "text": f"*제목:*\n{title}"},
                    {"type": "mrkdwn", "text": f"*담당자:*\n{user}"}
                ]),
                cls.create_section(fields=[
                    {"type": "mrkdwn", "text": f"*카테고리:*\n{category}"},
                    {"type": "mrkdwn", "text": f"*예상 소요 시간:*\n{weight}"}
                ]),
                cls.create_section(text=f"👉 <{url}|태스크 보러가기>"),
                cls.create_divider()
            ]
        } 