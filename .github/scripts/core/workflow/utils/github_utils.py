"""
GitHub API 관련 유틸리티 함수
"""
import time
from typing import Callable, Any, Optional
from github import GithubException
from .logger import logger

def retry_api_call(func: Callable, max_retries: int = 3, delay: int = 5) -> Optional[Any]:
    """
    GitHub API 호출을 재시도하는 데코레이터
    
    Args:
        func: 실행할 함수
        max_retries: 최대 재시도 횟수
        delay: 재시도 간 대기 시간(초)
    """
    for attempt in range(max_retries):
        try:
            return func()
        except GithubException as e:
            if e.status == 503 and attempt < max_retries - 1:
                logger.debug(f"\n[재시도] GitHub API 호출 실패 (시도 {attempt + 1}/{max_retries})")
                logger.debug(f"오류 메시지: {str(e)}")
                logger.debug(f"{delay}초 후 재시도합니다...")
                time.sleep(delay)
                continue
            raise
    return None 