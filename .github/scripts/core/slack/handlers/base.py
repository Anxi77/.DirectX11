"""
기본 이벤트 핸들러
"""
from typing import Dict
from ..client import SlackClient

class BaseHandler:
    """기본 Slack 이벤트 핸들러"""
    
    def __init__(self, client: SlackClient):
        self.client = client
    
    def handle(self, event_data: Dict):
        """이벤트 처리"""
        raise NotImplementedError("Subclasses must implement handle()") 