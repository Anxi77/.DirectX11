"""
리포트 메시지 포맷터
"""
from typing import Dict, List
from .base import BaseFormatter

class ReportFormatter(BaseFormatter):
    """리포트 관련 메시지 포맷팅"""
    
    @classmethod
    def format_daily_report(cls, tasks: List[Dict]) -> List[Dict]:
        """데일리 리포트 메시지 포맷팅"""
        if not tasks:
            return [
                cls.create_header("📊 일일 개발 로그"),
                cls.create_section(text="*오늘은 완료된 태스크가 없습니다.*"),
                cls.create_divider()
            ]
        
        return [
            cls.create_header("📊 새로운 일일 개발 로그가 생성되었습니다"),
            cls.create_section(
                text=f"*{tasks[0]['title']}*\n\n👉 <{tasks[0]['html_url']}|로그 보러가기>"
            ),
            cls.create_divider()
        ] 