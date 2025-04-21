"""
기본 메시지 포맷터
"""
from typing import Dict, List

class BaseFormatter:
    """기본 Slack 메시지 포맷터"""
    
    @staticmethod
    def create_header(text: str) -> Dict:
        """헤더 블록 생성"""
        return {
            "type": "header",
            "text": {"type": "plain_text", "text": text}
        }
    
    @staticmethod
    def create_section(text: str = None, fields: List[Dict] = None) -> Dict:
        """섹션 블록 생성"""
        section = {"type": "section"}
        if text:
            section["text"] = {"type": "mrkdwn", "text": text}
        if fields:
            section["fields"] = fields
        return section
    
    @staticmethod
    def create_divider() -> Dict:
        """구분선 블록 생성"""
        return {"type": "divider"} 