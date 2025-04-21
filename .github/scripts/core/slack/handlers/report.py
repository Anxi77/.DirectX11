"""리포트 이벤트 핸들러"""
from typing import Dict
import os
from .base import BaseHandler
from core.github.handlers.project_handler import GitHubProjectHandler as GitHubProjectManager
from core.task.handlers.task_handler import TaskHandler as TaskManager
from core.task.formatters.report_formatter import ReportFormatter as TaskReportFormatter

class ReportHandler(BaseHandler):
    def __init__(self, client, task_manager: GitHubProjectManager):
        super().__init__(client)
        self.github_manager = task_manager
    
    def handle(self, event_data: Dict = None):
        """일일 리포트 처리"""
        repo_name = os.environ.get('GITHUB_REPOSITORY', '').split('/')[-1]
        
        # 프로젝트 데이터 수집
        project_items = self.github_manager.get_project_items()
        task_issues = self.github_manager.get_task_issues()
        
        # 태스크 관리자 초기화
        task_manager = TaskManager(project_items, task_issues)
        report_formatter = TaskReportFormatter(repo_name, task_manager)
        
        # 리포트 데이터 생성
        report_data = report_formatter.get_report_data()
        
        # Slack 메시지 포맷팅
        message = {
            "blocks": [
                self._create_header("📊 일일 프로젝트 진행 현황 리포트"),
                self._create_summary_section(report_data),
                *self._create_task_sections(report_data),
                self._create_footer(report_data)
            ]
        }
        self.client.send_pm_report(message)
    
    def _create_summary_section(self, report_data: Dict) -> Dict:
        """요약 섹션 생성"""
        total = report_data.get('total_tasks', 0)
        completed = report_data.get('completed_tasks', 0)
        in_progress = report_data.get('in_progress_tasks', 0)
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        return {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*전체 태스크:*\n{total}개"},
                {"type": "mrkdwn", "text": f"*완료된 태스크:*\n{completed}개"},
                {"type": "mrkdwn", "text": f"*진행중 태스크:*\n{in_progress}개"},
                {"type": "mrkdwn", "text": f"*진행률:*\n{completion_rate:.1f}%"}
            ]
        }
    
    def _create_task_sections(self, report_data: Dict) -> list:
        """태스크 섹션 생성"""
        sections = []
        
        if completed_today := report_data.get('completed_today', []):
            sections.append({"type": "header", "text": {"type": "plain_text", "text": "✅ 오늘 완료된 태스크"}})
            for task in completed_today:  # 모든 완료된 태스크 표시
                sections.append({
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*태스크:*\n{task['title']}"},
                        {"type": "mrkdwn", "text": f"*완료 시각:*\n{task['completed_at'].split()[1]}"}  # 시간만 표시
                    ]
                })
        
        if in_progress_today := report_data.get('in_progress_today', []):
            sections.append({"type": "header", "text": {"type": "plain_text", "text": "⏳ 오늘 진행중인 태스크"}})
            for task in in_progress_today:  # 모든 진행중인 태스크 표시
                sections.append({
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*태스크:*\n{task['title']}"},
                        {"type": "mrkdwn", "text": f"*담당자:*\n{', '.join(task['assignees'])}"}
                    ]
                })
        
        return sections
    
    def _create_footer(self, report_data: Dict) -> Dict:
        """푸터 섹션 생성"""
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"👉 <{report_data.get('report_url', '')}|상세 보고서 보기>"
            }
        } 