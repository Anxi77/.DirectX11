"""
태스크 관리 핸들러
"""
import os
import re
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
from ..models.task import TodoInfo, TaskInfo
from ..models.status import TaskStatus, TaskState
from ..models.constants import TASK_CATEGORIES
from config.user_mappings import get_user_info

class TaskHandler:
    def __init__(self, project_items: Dict, task_issues: Dict):
        self.project_items = project_items
        self.task_issues = task_issues
        self.task_mapping = self._build_task_mapping()
        self.category_mapping = self._build_category_mapping()

    def _build_task_mapping(self) -> Dict[str, Dict]:
        """상위 태스크와 하위 투두 아이템 매핑을 구축"""
        mapping = {}
        task_count = 0
        todo_count = 0
        
        # 프로젝트 아이템들에서 [태스크명]을 추출하여 매핑
        for item_data in self.project_items.values():
            title = item_data['title']
            match = re.match(r'\[(.*?)\]', title)
            if match:
                task_name = match.group(1)
                todo_count += 1
                
                # 해당 태스크가 없으면 생성
                if task_name not in mapping:
                    task_count += 1
                    task_info = self.task_issues.get(task_name, {})
                    
                    mapping[task_name] = {
                        'number': task_info.get('number', task_count),
                        'title': task_name,
                        'todos': [],
                        'assignees': set(),
                        'state': task_info.get('state', 'OPEN'),
                        'completed_todos': 0,
                        'total_todos': 0,
                        'expected_time': task_info.get('expected_time', '-'),
                        'url': task_info.get('url', '#'),
                        'labels': item_data.get('labels', [])
                    }
                
                # 투두 정보 추가
                todo_info = TodoInfo(
                    title=title.replace(f'[{task_name}] ', ''),
                    number=item_data['number'],
                    status='Done' if item_data['state'] == 'CLOSED' else 'In Progress',
                    weight=1,
                    assignees=set(a['login'] for a in item_data['assignees']),
                    closed_at=item_data['closed_at']
                )
                
                mapping[task_name]['todos'].append(todo_info)
                mapping[task_name]['assignees'].update(todo_info.assignees)
                mapping[task_name]['total_todos'] += 1
                if todo_info.status == 'Done':
                    mapping[task_name]['completed_todos'] += 1
        
        return mapping

    def _build_category_mapping(self) -> Dict[str, List[TaskInfo]]:
        """카테고리별 태스크 매핑을 구축"""
        # 모든 카테고리 초기화
        mapping = {
            category: []
            for category in TASK_CATEGORIES.keys()
        }
        
        repo_name = os.environ.get('GITHUB_REPOSITORY')
        
        for task_name, task_data in self.task_mapping.items():
            # 태스크 카테고리 결정 (기본값: "기능 개발")
            category = "기능 개발"
            for label in task_data.get('labels', []):
                if label.startswith('category:'):
                    cat_name = label.replace('category:', '').strip()
                    # 카테고리가 TASK_CATEGORIES에 있는지 확인
                    if cat_name in TASK_CATEGORIES:
                        category = cat_name
                        break
            
            task_info = TaskInfo(
                number=task_data['number'] or 0,
                title=task_name,
                status=self.get_task_status(task_name),
                assignees=task_data['assignees'],
                priority="보통",
                expected_time=task_data['expected_time'],
                todos=task_data['todos'],
                category=category,
                url=f"https://github.com/{repo_name}/issues/{task_data['number']}"
            )
            mapping[category].append(task_info)
        
        return mapping

    def get_task_status(self, task_name: str) -> TaskStatus:
        """태스크의 상태를 계산합니다."""
        task_data = self.task_mapping.get(task_name)
        if not task_data:
            return TaskStatus(TaskState.WAITING, 0.0)
        
        total = task_data['total_todos']
        completed = task_data['completed_todos']
        
        if total == 0:
            return TaskStatus(TaskState.WAITING, 0.0)
        
        progress = (completed / total) * 100
        
        if progress == 100:
            return TaskStatus(TaskState.COMPLETED, progress)
        elif progress > 0:
            return TaskStatus(TaskState.IN_PROGRESS, progress)
        return TaskStatus(TaskState.WAITING, 0.0)

    def get_tasks_by_category(self, category: str) -> List[TaskInfo]:
        """카테고리별 태스크 목록 반환"""
        return self.category_mapping.get(category, [])

    def get_all_completed_todos(self) -> List[Tuple[datetime, TodoInfo, str]]:
        """완료된 모든 투두 목록을 날짜순으로 반환"""
        completed_todos = []
        
        for task_name, task_data in self.task_mapping.items():
            for todo in task_data['todos']:
                if todo.status == 'Done' and todo.closed_at:
                    date = datetime.fromisoformat(todo.closed_at.replace('Z', '+00:00'))
                    completed_todos.append((date, todo, task_name))
        
        return sorted(completed_todos, key=lambda x: x[0], reverse=True)

    def get_user_branch_url(self, username: str) -> str:
        """사용자의 개발 브랜치 URL을 생성합니다."""
        repo_name = os.environ.get('GITHUB_REPOSITORY')
        user_info = get_user_info(username)
        branch_suffix = user_info.get('branch_suffix', username)
        branch_name = f"Dev_{branch_suffix}"
        return f"https://github.com/{repo_name}/tree/{branch_name}" 