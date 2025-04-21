"""
보고서 포맷팅을 담당하는 모듈
"""
from datetime import datetime
from typing import Dict, Set
from ...task.models.status import TaskState, ReportSection
from ...task.models.constants import TASK_CATEGORIES
from config.user_mappings import GITHUB_USER_MAPPING

class ReportFormatter:
    def __init__(self, project_name: str, task_manager):
        self.project_name = project_name
        self.task_manager = task_manager
        self.current_date = datetime.now().strftime('%Y-%m-%d')

    def format_report(self) -> str:
        """전체 보고서를 포맷팅합니다."""
        return f"""<div align="center">\n
{self._format_header()}
</div>

{self._format_basic_info()}
{self._format_team_info()}
{self._format_task_details()}
{self._format_progress_section()}
{self._format_task_history()}
{self._format_risks()}

---
> 이 보고서는 자동으로 생성되었으며, 담당자가 지속적으로 업데이트할 예정입니다.
"""

    def _format_header(self) -> str:
        """보고서 헤더를 생성합니다."""
        return """![header](https://capsule-render.vercel.app/api?type=transparent&color=39FF14&height=150&section=header&text=Project%20Report&fontSize=50&animation=fadeIn&fontColor=39FF14&desc=프로젝트%20진행%20보고서&descSize=25&descAlignY=75)

# 📊 프로젝트 진행보고서

"""

    def _format_basic_info(self) -> str:
        """기본 정보 섹션을 생성합니다."""
        return f"""## 📌 기본 정보

**프로젝트명**: {self.project_name}  
**보고서 최종 업데이트**: {self.current_date}  
**프로젝트 기간**: 진행중"""

    def _format_team_info(self) -> str:
        """팀원 정보 섹션을 생성합니다."""
        team_section = """## 👥 팀원 정보

| 깃허브 | 이름 | 역할 |
|--------|------|------|"""
        
        for username, info in GITHUB_USER_MAPPING.items():
            team_section += f"\n| @{username} | {info['name']} | {info['role']} |"
        
        return team_section

    def _format_task_details(self) -> str:
        """태스크 상세 내역을 포맷팅합니다."""
        details = "## 📋 태스크 상세 내역\n\n"
        
        # 각 카테고리별로 섹션 생성
        for category, info in TASK_CATEGORIES.items():
            details += f"""<details>
<summary><h3>{info['emoji']} {category}</h3></summary>

| 태스크 ID | 태스크명 | 담당자 | 예상 시간 | 실제 시간 | 진행 상태 | 우선순위 |
| --------- | -------- | ------ | --------- | --------- | --------- | -------- |"""
            
            tasks = self.task_manager.get_tasks_by_category(category)
            if tasks:
                for task in tasks:
                    assignees_str = self._format_assignees(task.assignees)
                    status_text = f"{task.status.state.icon} ({task.status.progress:.1f}%)"
                    details += f"\n| [TSK-{task.number}]({task.url}) | {task.title} | {assignees_str} | {task.expected_time} | - | {status_text} | {task.priority} |"
            
            details += "\n</details>\n"
        
        return details.rstrip()

    def _format_progress_section(self) -> str:
        """진행 현황 섹션을 생성합니다."""
        return f"""\n## 📊 진행 현황 요약\n

### 전체 진행률

{self._format_overall_progress()}

{self._format_category_progress()}

{self._format_daily_status()}"""

    def _format_overall_progress(self) -> str:
        """전체 진행률 섹션을 생성합니다."""
        stats = self._calculate_overall_stats()
        total = stats['total']
        completed = stats['completed']
        in_progress = stats['in_progress']

        progress = (completed / total * 100) if total > 0 else 0
        in_progress_rate = (in_progress / total * 100) if total > 0 else 0
        waiting_rate = ((total - completed - in_progress) / total * 100) if total > 0 else 100

        return f"""전체 진행 상태: {completed}/{total} 완료 ({progress:.1f}%)

```mermaid
pie title 전체 진행 현황
    "완료" : {progress:.1f}
    "진행중" : {in_progress_rate:.1f}
    "대기중" : {waiting_rate:.1f}
```"""

    def _format_category_progress(self) -> str:
        """카테고리별 진행 현황을 생성합니다."""
        stats = {}
        for category in TASK_CATEGORIES:
            tasks = self.task_manager.get_tasks_by_category(category)
            completed = sum(1 for task in tasks if task.status.state == TaskState.COMPLETED)
            in_progress = sum(1 for task in tasks if task.status.state == TaskState.IN_PROGRESS)
            total = len(tasks)
            
            if total > 0:
                progress_rate = (completed / total) * 100
            else:
                progress_rate = 0.0
            
            stats[category] = {
                'total': total,
                'completed': completed,
                'in_progress': in_progress,
                'progress_rate': progress_rate
            }
        
        # 테이블 형식으로 출력
        progress = """### 📊 카테고리별 진행 현황

| 카테고리 | 완료 | 진행중 | 대기중 | 진행률 |
| -------- | ---- | ------ | ------ | ------ |"""
        
        # 진행률 기준으로 정렬
        sorted_categories = sorted(stats.items(), key=lambda x: (-x[1]['progress_rate'], x[0]))
        
        for category, stat in sorted_categories:
            waiting = stat['total'] - stat['completed'] - stat['in_progress']
            progress += f"\n| {TASK_CATEGORIES[category]['emoji']} {category} | {stat['completed']} | {stat['in_progress']} | {waiting} | {stat['progress_rate']:.1f}% |"
        
        # 진행률 차트 추가
        progress += "\n\n```mermaid\npie title 카테고리별 진행률\n"
        has_progress = False
        for category, stat in sorted_categories:
            if stat['progress_rate'] > 0:
                has_progress = True
                progress += f"    \"{TASK_CATEGORIES[category]['emoji']} {category}\" : {stat['progress_rate']:.1f}\n"
        if not has_progress:
            progress += "    \"진행중인 카테고리 없음\" : 100\n"
        progress += "```"
        
        return progress

    def _format_daily_status(self) -> str:
        """일자별 상세 현황을 생성합니다."""
        daily_stats = self._calculate_daily_stats()
        
        status = """### 📅 일자별 상세 현황

| 날짜 | 완료된 태스크 | 신규 태스크 | 진행중 태스크 |
| ---- | ------------- | ----------- | ------------- |"""
        
        sorted_dates = sorted(daily_stats.items(), reverse=True)
        for date, stats in sorted_dates:
            status += f"\n| {date} | {stats['completed']} | {stats['new']} | {stats['in_progress']} |"
        
        # 일자별 추이 차트 추가
        status += "\n\n```mermaid\ngantt\n    title 일자별 태스크 현황\n"
        status += "    dateFormat YYYY-MM-DD\n"
        
        for date, stats in sorted_dates:
            if stats['completed'] > 0:
                status += f"    section {date}\n"
                status += f"    완료된 태스크 ({stats['completed']}) : done, {date}, 1d\n"
            if stats['in_progress'] > 0:
                status += f"    진행중 태스크 ({stats['in_progress']}) : active, {date}, 1d\n"
        
        status += "```"
        return status

    def _format_task_history(self) -> str:
        """태스크 완료 히스토리를 생성합니다."""
        completed_todos = self.task_manager.get_all_completed_todos()
        
        history = "## 📅 태스크 완료 히스토리\n\n"
        if not completed_todos:
            return history + "아직 완료된 태스크가 없습니다."
        
        current_date = None
        for date, todo, task_name in completed_todos:
            date_str = date.strftime('%Y-%m-%d')
            if date_str != current_date:
                if current_date:
                    history += "</details>\n\n"
                count = sum(1 for d, _, _ in completed_todos if d.strftime('%Y-%m-%d') == date_str)
                history += f'<details>\n<summary><h3 style="display: inline;">📆 {date_str} ({count}개)</h3></summary>\n\n'
                history += "| 투두 ID | 투두명 | 상위 태스크 | 담당자 |\n|---------|--------|-------------|--------|\n"
                current_date = date_str
            
            assignees_str = self._format_assignees(todo.assignees)
            history += f"| #{todo.number} | {todo.title} | {task_name} | {assignees_str} |\n"
        
        if current_date:
            history += "</details>\n"
        
        return history

    def _format_risks(self) -> str:
        """특이사항 및 리스크 섹션을 생성합니다."""
        return """## 📝 특이사항 및 리스크

| 구분 | 내용 | 대응 방안 |
| ---- | ---- | --------- |
| - | - | - |"""

    def _format_assignees(self, assignees: Set[str]) -> str:
        """담당자 목록을 포맷팅합니다."""
        if not assignees:
            return "-"
        
        formatted = []
        for username in sorted(assignees):
            if username in GITHUB_USER_MAPPING:
                user_info = GITHUB_USER_MAPPING[username]
                branch_url = self.task_manager.get_user_branch_url(username)
                formatted.append(f"[{user_info['name']}]({branch_url})")
                continue
            formatted.append(f"@{username}")
        
        return ", ".join(formatted)

    def _calculate_overall_stats(self) -> Dict:
        """전체 통계를 계산합니다."""
        total_stats = {'total': 0, 'completed': 0, 'in_progress': 0}
        
        for category in TASK_CATEGORIES:
            tasks = self.task_manager.get_tasks_by_category(category)
            total_stats['total'] += len(tasks)
            total_stats['completed'] += sum(1 for task in tasks if task.status.state == TaskState.COMPLETED)
            total_stats['in_progress'] += sum(1 for task in tasks if task.status.state == TaskState.IN_PROGRESS)
        
        return total_stats

    def _calculate_daily_stats(self) -> Dict:
        """일자별 통계를 계산합니다."""
        stats = {}
        today = datetime.now().strftime('%Y-%m-%d')
        stats[today] = {'completed': 0, 'new': 0, 'in_progress': 0}
        
        # 완료된 투두 카운트
        completed_todos = self.task_manager.get_all_completed_todos()
        for date, _, _ in completed_todos:
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in stats:
                stats[date_str] = {'completed': 0, 'new': 0, 'in_progress': 0}
            stats[date_str]['completed'] += 1
        
        # 진행중인 투두 카운트
        for category in TASK_CATEGORIES:
            tasks = self.task_manager.get_tasks_by_category(category)
            stats[today]['in_progress'] += sum(1 for task in tasks if task.status.state == TaskState.IN_PROGRESS)
        
        return stats 