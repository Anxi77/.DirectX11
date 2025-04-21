"""
제안서 메시지 포맷터
"""
from typing import Dict
from .base import BaseFormatter

class ProposalFormatter(BaseFormatter):
    """제안서 관련 메시지 포맷팅"""
    
    STATUS_INFO = {
        '✅ 승인완료': ("✅ 태스크 제안서가 승인되었습니다", "승인완료"),
        '❌ 반려': ("❌ 태스크 제안서가 반려되었습니다", "반려"),
        '⏸️ 보류': ("⏸️ 태스크 제안서가 보류되었습니다", "보류"),
        '⌛ 검토대기': ("📝 새로운 태스크 제안서가 등록되었습니다", "검토대기")
    }
    
    @classmethod
    def format_proposal(cls, proposal: Dict, event_type: str) -> Dict:
        """제안서 메시지 포맷팅"""
        title = proposal['title']
        url = proposal['html_url']
        user = proposal['user']['login']
        labels = [label['name'] for label in proposal.get('labels', [])]
        
        for label, (header, status) in cls.STATUS_INFO.items():
            if label in labels:
                break
        else:
            header, status = cls.STATUS_INFO['⌛ 검토대기']
        
        return {
            "blocks": [
                cls.create_header(header),
                cls.create_section(fields=[
                    {"type": "mrkdwn", "text": f"*제목:*\n{title}"},
                    {"type": "mrkdwn", "text": f"*제안자:*\n{user}"}
                ]),
                cls.create_section(fields=[
                    {"type": "mrkdwn", "text": f"*상태:*\n{status}"}
                ]),
                cls.create_section(text=f"👉 <{url}|제안서 보러가기>"),
                cls.create_divider()
            ]
        } 