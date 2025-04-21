"""
날짜 처리 관련 유틸리티 함수
"""
from datetime import datetime
import pytz
from typing import Tuple

def get_current_time(timezone: str = 'Asia/Seoul') -> Tuple[datetime, str]:
    """
    현재 시간과 날짜 문자열을 반환합니다.
    
    Args:
        timezone: 타임존 문자열 (기본값: 'Asia/Seoul')
        
    Returns:
        (현재 시간 객체, YYYY-MM-DD 형식의 날짜 문자열)
    """
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    date_string = now.strftime('%Y-%m-%d')
    return now, date_string

def format_issue_title(date_string: str, repo_name: str = '', prefix: str = '📅') -> str:
    """
    DSR 이슈 제목을 생성합니다.
    
    Args:
        date_string: YYYY-MM-DD 형식의 날짜 문자열
        repo_name: 저장소 이름 (선택)
        prefix: 이슈 제목 접두어 (기본값: '📅')
        
    Returns:
        포맷팅된 이슈 제목
    """
    title = f"{prefix} Development Status Report ({date_string})"
    if repo_name:
        if repo_name.startswith('.'):
            repo_name = repo_name[1:]
        title += f" - {repo_name}"
    return title 