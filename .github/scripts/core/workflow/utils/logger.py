"""
워크플로우 로깅을 담당하는 유틸리티
"""
import logging

class WorkflowLogger:
    def __init__(self):
        self.logger = logging.getLogger('workflow_tracker')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('=== %(message)s ===')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def section(self, title: str, message: str = '') -> None:
        self.logger.info(f"{title}")
        if message:
            print(f"{message}")
    
    def commit(self, action: str, sha: str, message: str, extra: str = '') -> None:
        print(f"{action}: [{sha[:7]}] {message}{' - ' + extra if extra else ''}")
    
    def todo(self, status: str, text: str) -> None:
        print(f"{status}: {text}")
    
    def debug(self, message: str) -> None:
        print(f"DEBUG: {message}")
        
    def error(self, message: str) -> None:
        print(f"ERROR: {message}")

logger = WorkflowLogger() 