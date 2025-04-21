"""
TODO 처리를 담당하는 핸들러
"""
from typing import Dict, List, Tuple, Optional
from github.Repository import Repository
from github.Issue import Issue
from ..utils.logger import logger

class TodoProcessor:
    def __init__(self, repo: Repository, issue_number: Optional[int] = None):
        self.repo = repo
        self.issue_number = issue_number
        self.category_stack = []
        self.issue_category_map = {}
        self.category_order = []
        self._current_category = 'General'
        self.category_todos = {'General': []}  # 카테고리별 TODO 항목 저장
    
    @property
    def current_category(self) -> str:
        """현재 활성화된 카테고리를 반환합니다."""
        return self._current_category
    
    @current_category.setter
    def current_category(self, value: str) -> None:
        """현재 카테고리를 설정합니다."""
        self._current_category = value
        if value not in self.category_order and value != 'General':
            self.category_order.append(value)
        if value not in self.category_todos:
            self.category_todos[value] = []
    
    def push_category(self, category: str) -> None:
        """카테고리 스택에 새 카테고리를 추가합니다."""
        self.category_stack.append(category)
        self.current_category = category
        logger.debug(f"[push_category] 카테고리 추가: {category}")
    
    def pop_category(self) -> Optional[str]:
        """카테고리 스택에서 현재 카테고리를 제거합니다."""
        if self.category_stack:
            removed = self.category_stack.pop()
            self.current_category = self.category_stack[-1] if self.category_stack else 'General'
            logger.debug(f"[pop_category] 카테고리 제거: {removed}, 현재 카테고리: {self.current_category}")
            return removed
        return None
    
    def map_issue_to_category(self, issue_number: str, category: str) -> None:
        """이슈 번호와 카테고리를 매핑합니다."""
        if not issue_number.startswith('#'):
            issue_number = f"#{issue_number}"
        if issue_number not in self.issue_category_map:
            self.issue_category_map[issue_number] = category
            logger.debug(f"[map_issue_to_category] 이슈 {issue_number}를 카테고리 {category}에 매핑")
    
    def get_issue_category(self, issue_number: str) -> str:
        """이슈의 카테고리를 반환합니다."""
        if not issue_number.startswith('#'):
            issue_number = f"#{issue_number}"
        return self.issue_category_map.get(issue_number, self.current_category)
    
    @staticmethod
    def is_issue_todo(todo_text: str) -> bool:
        """TODO 항목이 이슈 생성이 필요한지 확인합니다."""
        return todo_text.strip().startswith('(issue)')
    
    def _process_line(self, line: str, checked: bool = False) -> Tuple[bool, str, str]:
        """한 줄의 텍스트를 처리하고 카테고리와 함께 반환합니다."""
        line = line.strip()
        if not line:
            return False, '', ''
            
        if line.startswith('@'):
            category = line[1:].strip()
            self.push_category(category)
            return checked, line, category
            
        if line.startswith('#'):
            # 이슈 번호인 경우 매핑된 카테고리 사용
            category = self.get_issue_category(line)
            if category not in self.category_todos:
                self.category_todos[category] = []
            return checked, line, category
            
        if line.startswith(('-', '*')):
            line = line[1:].strip()
            
        return checked, line, self.current_category
    
    def _add_to_category(self, checked: bool, text: str, category: str) -> None:
        """TODO 항목을 해당 카테고리에 추가합니다."""
        if category not in self.category_todos:
            self.category_todos[category] = []
            
        if text.startswith('#'):
            self.map_issue_to_category(text, category)
            
        # 중복 체크
        if text not in [t for _, t in self.category_todos[category]]:
            self.category_todos[category].append((checked, text))
            logger.debug(f"[add_to_category] {text} 추가됨 (카테고리: {category})")
    
    def process_todo_message(self, todo_text: str) -> List[Tuple[bool, str]]:
        """커밋 메시지의 TODO 섹션을 처리합니다."""
        if not todo_text:
            return []
            
        self.category_stack.clear()
        self.category_todos.clear()
        self.category_todos['General'] = []
        
        todo_lines = []
        logger.debug(f"[process_todo_message] 시작 - 초기 카테고리: {self.current_category}")
        
        for line in todo_text.strip().split('\n'):
            checked, text, category = self._process_line(line)
            if text:
                if text.startswith('@'):
                    todo_lines.append((checked, text))
                else:
                    self._add_to_category(checked, text, category)
                    todo_lines.append((checked, text))
        
        logger.debug(f"[process_todo_message] 완료 - 최종 카테고리: {self.current_category}")
        return todo_lines
    
    def process_existing_todos(self, existing_todos: List[Tuple[bool, str]]) -> List[Tuple[bool, str]]:
        """기존 TODO 항목들을 처리합니다."""
        if not existing_todos:
            return []
            
        self.category_stack.clear()
        self.category_todos.clear()
        self.category_todos['General'] = []
        
        processed = []
        logger.debug("[process_existing_todos] 처리 시작")
        
        # 첫 번째 패스: 카테고리 구조 생성 및 이슈 매핑
        for checked, text in existing_todos:
            checked, text, category = self._process_line(text, checked)
            if text:
                if text.startswith('@'):
                    processed.append((checked, text))
                else:
                    self._add_to_category(checked, text, category)
                    processed.append((checked, text))
        
        return processed
    
    def merge_todos(self, existing_todos: List[Tuple[bool, str]], new_todos: List[Tuple[bool, str]]) -> List[Tuple[bool, str]]:
        """기존 TODO와 새로운 TODO를 병합합니다."""
        merged_todos = []
        
        logger.debug("[merge_todos] 병합 시작")
        logger.debug(f"[merge_todos] 기존 TODO 수: {len(existing_todos)}")
        logger.debug(f"[merge_todos] 새로운 TODO 수: {len(new_todos)}")
        
        # 기존 TODO 처리
        for checked, text in existing_todos:
            checked, text, category = self._process_line(text, checked)
            if text:
                if text.startswith('@'):
                    merged_todos.append((checked, text))
                else:
                    self._add_to_category(checked, text, category)
        
        # 새로운 TODO 처리
        for checked, text in new_todos:
            checked, text, category = self._process_line(text, checked)
            if text:
                if text.startswith('@'):
                    merged_todos.append((checked, text))
                else:
                    self._add_to_category(checked, text, category)
        
        # 결과 병합 (카테고리 순서 유지)
        logger.debug("[merge_todos] 카테고리별 TODO 병합 결과:")
        for category in self.category_order:
            todos = self.category_todos.get(category, [])
            logger.debug(f"- {category}: {len(todos)}개 항목")
            if todos:
                merged_todos.append((False, f"@{category}"))
                merged_todos.extend(todos)
        
        # General 카테고리 항목 추가
        if self.category_todos.get('General', []):
            todos = self.category_todos['General']
            logger.debug(f"- General: {len(todos)}개 항목")
            merged_todos.extend(todos)
        
        return merged_todos
    
    def convert_to_checkbox_list(self, text: str) -> str:
        """텍스트를 체크박스 목록으로 변환합니다."""
        if not text:
            return ''
        
        self.category_todos.clear()
        self.category_todos['General'] = []
        
        # TODO 항목 수집
        for line in text.strip().split('\n'):
            checked, text, category = self._process_line(line)
            if text and not text.startswith('@'):
                self._add_to_category(checked, text, category)
        
        # 카테고리별 출력
        lines = []
        for category in self.category_order:
            todos = self.category_todos.get(category, [])
            if todos:
                total_todos = len(todos)
                checked_todos = sum(1 for _, todo in todos if todo.startswith('#'))
                lines.append(f"\n📑 {category} ({checked_todos}/{total_todos})\n")
                for checked, todo in todos:
                    if todo.startswith('#'):
                        lines.append(todo)
                    else:
                        lines.append(f"- [ ] {todo}")
        
        # General 카테고리 처리
        if self.category_todos['General']:
            todos = self.category_todos['General']
            total_todos = len(todos)
            checked_todos = sum(1 for _, todo in todos if todo.startswith('#'))
            lines.append(f"\n📑 General ({checked_todos}/{total_todos})\n")
            for checked, todo in todos:
                if todo.startswith('#'):
                    lines.append(todo)
                else:
                    lines.append(f"- [ ] {todo}")
        
        return '\n'.join(lines)
    
    def process_todos(self, commit_data: Optional[Dict] = None, existing_todos: Optional[List[Tuple[bool, str]]] = None, is_new_day: bool = False) -> Tuple[List[Tuple[bool, str]], List[Issue]]:
        """TODO 항목들을 처리합니다."""
        all_todos = []
        created_issues = []
        
        logger.debug(f"[process_todos] 시작 - is_new_day: {is_new_day}")
        
        # 기존 TODO 처리
        if existing_todos:
            logger.debug(f"[process_todos] 기존 TODO 처리 시작 (총 {len(existing_todos)}개)")
            if is_new_day:
                filtered_todos = [(checked, text) for checked, text in existing_todos 
                                if not checked or text.startswith('@')]
                logger.debug(f"[process_todos] 새로운 날짜로 인한 필터링 후 TODO: {len(filtered_todos)}개")
                all_todos.extend(filtered_todos)
            else:
                processed = self.process_existing_todos(existing_todos)
                logger.debug(f"[process_todos] 기존 TODO 처리 완료: {len(processed)}개")
                all_todos.extend(processed)
        
        # 새로운 TODO 처리
        if commit_data and commit_data.get('todo'):
            logger.debug("[process_todos] 새로운 커밋의 TODO 처리 시작")
            new_todos = self.process_todo_message(commit_data['todo'])
            logger.debug(f"[process_todos] 새로운 TODO 발견: {len(new_todos)}개")
            all_todos = self.merge_todos(all_todos, new_todos)
        
        # 최종 처리 및 이슈 생성
        logger.debug("[process_todos] 최종 TODO 처리 시작")
        processed_todos = []
        for checked, text in all_todos:
            if text.startswith('@'):
                category = text[1:].strip()
                self.push_category(category)
                processed_todos.append((checked, text))
            elif self.is_issue_todo(text):
                logger.debug(f"[process_todos] 이슈 생성 시도 (카테고리: {self.current_category}): {text}")
                new_issue = self.create_issue_from_todo(text)
                if new_issue:
                    logger.debug(f"[process_todos] 이슈 생성 성공: #{new_issue.number}")
                    created_issues.append(new_issue)
                    processed_todos.append((checked, f"#{new_issue.number}"))
            else:
                processed_todos.append((checked, text))
        
        logger.debug(f"[process_todos] 완료 - 생성된 이슈: {len(created_issues)}개")
        return processed_todos, created_issues
    
    def create_issue_from_todo(self, todo_text: str) -> Optional[Issue]:
        """TODO 항목으로부터 새 이슈를 생성합니다."""
        if not self.is_issue_todo(todo_text):
            return None
            
        title = todo_text.replace('(issue)', '', 1).strip()
        
        # 현재 카테고리가 설정되어 있지 않으면 기본값 사용
        if not self.current_category or self.current_category == 'General':
            logger.debug(f"카테고리가 설정되지 않아 기본값 'General'을 사용합니다.")
            self.current_category = 'General'
            
        issue_title = f"[{self.current_category}] {title}"
        logger.debug(f"이슈 생성: {issue_title} (카테고리: {self.current_category})")
        
        try:
            new_issue = self.repo.create_issue(
                title=issue_title,
                body=self._create_issue_body(title),
                labels=['todo-generated', f'category:{self.current_category}']
            )
            
            if self.issue_number:
                parent_issue = self.repo.get_issue(self.issue_number)
                parent_issue.create_comment(f"Created issue #{new_issue.number} from todo item")
                
            return new_issue
        except Exception as e:
            logger.error(f"Failed to create issue for todo: {title}")
            logger.error(f"Error: {str(e)}")
            return None
    
    def _create_issue_body(self, title: str) -> str:
        """이슈 본문을 생성합니다."""
        return f"""## 📌 Task Description
{title}

## 🏷 Category
{self.current_category}

## 🔗 References
- Created from Daily Log: #{self.issue_number}""" 