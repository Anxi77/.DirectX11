"""제안서 이벤트 핸들러"""
from typing import Dict
from .base import BaseHandler
from ..formatters.proposal import ProposalFormatter

class ProposalHandler(BaseHandler):
    def handle(self, event_data: Dict):
        """제안서 이벤트 처리"""
        proposal_data = event_data['issue']
        event_type = event_data['action']
        message = ProposalFormatter.format_proposal(proposal_data, event_type)
        self.client.send_channel_notification(id,message) 