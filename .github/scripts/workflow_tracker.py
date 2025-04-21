"""
워크플로우 트래커 메인 스크립트
"""
import os
import re
from datetime import datetime
import pytz
from github import Github
from typing import List, Tuple, Optional
from github.Repository import Repository
from github.Issue import Issue
from core.workflow.utils.logger import logger
from core.workflow.models.commit import parse_commit_message
from core.workflow.handlers.commit_handler import CommitProcessor
from core.workflow.handlers.todo_handler import TodoProcessor
from core.workflow.formatters.commit_formatter import CommitSectionBuilder
from core.workflow.formatters.todo_formatter import create_todo_section

def find_active_dsr_issue(repo: Repository, date_string: str, issue_title: str) -> Optional[Issue]:
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

def main():
    github_token = os.environ.get('PAT') or os.environ['GITHUB_TOKEN']
    g = Github(github_token)
    repository = os.environ['GITHUB_REPOSITORY']
    repo = g.get_repo(repository)
    
    try:
        test_commit = repo.get_commits()[0]
        logger.debug(f"Repository access test - latest commit: {test_commit.sha[:7]}")
    except Exception as e:
        logger.error(f"Repository access error: {str(e)}")
    
    timezone = os.environ.get('TIMEZONE', 'Asia/Seoul')
    issue_prefix = os.environ.get('ISSUE_PREFIX', '📅')
    branch = os.environ['GITHUB_REF'].replace('refs/heads/', '')
    
    logger.debug(f"Current branch: {branch}")
    logger.debug(f"GITHUB_REF: {os.environ['GITHUB_REF']}")
    
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    date_string = now.strftime('%Y-%m-%d')
    
    repo_name = repository.split('/')[-1]
    if repo_name.startswith('.'):
        repo_name = repo_name[1:]

    issue_title = f"{issue_prefix} Development Status Report ({date_string})"
    if repo_name:
        issue_title += f" - {repo_name}"
    
    logger.section("Issue Title Format")
    logger.debug(f"Using title format: {issue_title}")

    commit_processor = CommitProcessor(repo, timezone)
    branches_commits = commit_processor.get_todays_commits()
    
    if not branches_commits:
        logger.debug("오늘 커밋된 내용이 없습니다")
        return

    today_issue = find_active_dsr_issue(repo, date_string, issue_title)
    
    todo_processor = TodoProcessor(repo, today_issue.number if today_issue else None)
    
    previous_todos = get_previous_dsr_todos(repo, date_string)
    
    existing_content = {'todos': previous_todos}
    if today_issue:
        today_content = parse_existing_issue(today_issue.body)
        existing_content['todos'] = todo_processor.merge_todos(previous_todos, today_content.get('todos', []))
    
    section_builder = CommitSectionBuilder(repo, timezone)
    branches_content = section_builder.create_branch_sections(branches_commits, existing_content)
    
    current_commit = repo.get_commit(os.environ['GITHUB_SHA'])
    commit_data = parse_commit_message(current_commit.commit.message)
    
    processed_todos, created_issues = todo_processor.process_todos(
        commit_data=commit_data,
        existing_todos=existing_content.get('todos', []),
        is_new_day=datetime.now(pytz.timezone(timezone)).strftime('%Y-%m-%d') != date_string
    )
    
    if created_issues:
        logger.section("Created new issues from todos")
        for issue in created_issues:
            print(f"#{issue.number}: {issue.title}")
    
    logger.section("Final Result")
    print(f"Total TODOs: {len(processed_todos)} items")
    
    body = f'''# {issue_title}

<div align="center">

## 📊 Branch Summary

</div>

{"\n\n".join(branches_content)}

<div align="center">

## 📝 Todo

{create_todo_section(processed_todos)}'''

    if today_issue:
        today_issue.edit(body=body)
        logger.debug(f"이슈 #{today_issue.number} 업데이트됨")
    else:
        new_issue = repo.create_issue(
            title=issue_title,
            body=body,
            labels=[os.environ.get('ISSUE_LABEL', 'dsr'), f"branch:{branch}"]
        )
        print(f"Created new issue #{new_issue.number}")

if __name__ == '__main__':
    main()