"""
DSR(Daily Status Report) 이슈 처리를 담당하는 핸들러
"""
from typing import Dict, List, Tuple, Optional
from github.Repository import Repository
from github.Issue import Issue
from ..utils.logger import logger
import re

def find_active_dsr_issue(repo: Repository, date_string: str, issue_title: str) -> Optional[Issue]:
    """활성화된 DSR 이슈를 찾습니다."""
    logger.section("Searching for Active DSR Issue")
    
    dsr_issues = repo.get_issues(state='open', labels=['DSR'])

    for issue in dsr_issues:
        logger.debug(f"Checking issue #{issue.number}: {issue.title}")
        if issue.title == issue_title:
            logger.debug(f"Found today's DSR issue: #{issue.number}")
            return issue
    
    logger.debug("No active DSR issue found for today")
    return None

def parse_existing_issue(body: str) -> dict:
    """이슈 본문을 파싱하여 TODO 항목과 카테고리를 추출합니다."""
    todos = []
    current_category = 'General'
    in_todo_section = False
    
    if not body:
        return {'todos': todos}
    
    for line in body.split('\n'):
        if '## 📝 Todo' in line:
            in_todo_section = True
        elif in_todo_section and line.strip() and line.startswith('##'):
            in_todo_section = False
        elif in_todo_section and line.strip():
            if '<summary><h3' in line:  # 카테고리 헤더 찾기
                category_match = re.search(r'📑\s*(.*?)\s*\(', line)
                if category_match:
                    current_category = category_match.group(1).strip()
                    todos.append((False, f"@{current_category}"))
            elif line.startswith('- ['):
                checked = 'x' in line[3]
                text = line[6:].strip()
                if text.startswith('#'):  # 이슈 참조인 경우
                    todos.append((checked, text))
                else:  # 일반 TODO 항목
                    todos.append((checked, text))
    
    return {'todos': todos}

def get_previous_dsr_todos(repo: Repository, current_date: str) -> List[Tuple[bool, str]]:
    """이전 일자의 미완료 TODO 항목을 가져오고 이슈를 닫습니다."""
    todos = []
    dsr_issues = repo.get_issues(state='open', labels=['DSR'])
    
    # 날짜순으로 정렬 (최신순)
    sorted_issues = sorted(
        [issue for issue in dsr_issues if "Development Status Report" in issue.title],
        key=lambda x: x.created_at,
        reverse=True
    )
    
    for issue in sorted_issues:
        if current_date in issue.title:  # 현재 날짜의 이슈는 건너뜀
            continue
            
        # 이전 이슈의 TODO 항목을 파싱
        previous_content = parse_existing_issue(issue.body)
        if previous_content and 'todos' in previous_content:
            # 미완료 항목과 카테고리만 가져옴
            for checked, text in previous_content['todos']:
                if text.startswith('@') or not checked:  # 카테고리이거나 미완료 항목
                    todos.append((checked, text))
            
            # 이전 이슈 닫기
            issue.edit(state='closed')
            logger.debug(f"이전 DSR 이슈 #{issue.number} 닫힘")
            
            break  # 가장 최근 이슈만 처리
    
    return todos 