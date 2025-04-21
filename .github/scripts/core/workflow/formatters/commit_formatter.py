"""
커밋 섹션 포맷팅을 담당하는 모듈
"""
import os
import re
from datetime import datetime
from typing import List
from github.Repository import Repository
import pytz
from ..models.commit import parse_commit_message
from ..utils.logger import logger
from ..utils.github_utils import retry_api_call

class CommitSectionBuilder:
    def __init__(self, repo: Repository, timezone: str):
        self.repo = repo
        self.tz = pytz.timezone(timezone)
        self.current_date = datetime.now(self.tz).strftime('%Y-%m-%d')
    
    def _format_body(self, body: str) -> str:
        """커밋 본문을 포맷팅합니다."""
        if not body:
            return '> No additional details provided.'
            
        body_lines = []
        for line in body.strip().split('\n'):
            line = line.strip()
            if line:
                if line.startswith('-'):
                    line = line[1:].strip()
                body_lines.append(f"> • {line}")
        
        return '\n'.join(body_lines)
    
    def _get_related_issues(self, message: str, commit_data: dict) -> List[str]:
        """관련된 이슈 참조를 찾습니다."""
        issue_numbers = set(re.findall(r'#(\d+)', message))
        related_issues = []
        
        dsr_issues = retry_api_call(lambda: list(self.repo.get_issues(state='open', labels=[os.environ.get('ISSUE_LABEL', 'dsr')])))
        current_dsr = next((issue for issue in dsr_issues if f"Daily Development Log ({self.current_date})" in issue.title), None)
        
        if current_dsr:
            issue_numbers.add(str(current_dsr.number))
        
        for issue_num in issue_numbers:
            try:
                issue = retry_api_call(lambda: self.repo.get_issue(int(issue_num)))
                if issue:
                    if current_dsr and str(issue.number) == str(current_dsr.number):
                        issue.create_comment(f"커밋이 추가되었습니다: {commit_data['title']}")
                    else:
                        issue.create_comment(f"Referenced in commit {commit_data['title']}")
                    related_issues.append(f"Related to #{issue_num}")
            except Exception as e:
                logger.debug(f"Failed to add comment to issue #{issue_num}: {str(e)}")
                continue
        
        return related_issues
    
    def create_section(self, commit_data: dict, branch: str, commit_sha: str, author: str, time_string: str) -> str:
        """커밋 섹션을 생성합니다."""
        logger.debug(f"Creating commit section for {commit_sha[:7]}")
        
        body = self._format_body(commit_data.get('body', ''))
        full_message = f"{commit_data['title']}\n{commit_data.get('body', '')}\n{commit_data.get('footer', '')}"
        related_issues = self._get_related_issues(full_message, commit_data)
        
        if related_issues:
            body += "\n> \n> Related Issues:\n> " + "\n> ".join(related_issues)
        
        return f'''> <details>
> <summary>💫 {time_string} - {commit_data['title'].strip()}</summary>
>
> Type: {commit_data['type']} ({commit_data['type_info']['description']})
> Commit: {commit_sha[:7]}
> Author: {author}
>
{body}
> </details>'''

    def create_branch_sections(self, branches_commits: dict, existing_content: dict = None) -> List[str]:
        """브랜치별 섹션을 생성합니다."""
        branches_content = existing_content.get('branches', {}) if existing_content else {}
        result = []
        
        for branch_name, commits in branches_commits.items():
            logger.debug(f"\n{branch_name} 브랜치 섹션 생성 중...")
            branch_sections = []
            
            for commit in commits:
                commit_data = parse_commit_message(commit.commit.message)
                if not commit_data:
                    continue
                
                commit_time = commit.commit.author.date.replace(tzinfo=pytz.UTC).astimezone(self.tz)
                commit_time_string = commit_time.strftime('%H:%M:%S')
                
                section = self.create_section(
                    commit_data,
                    branch_name,
                    commit.sha,
                    commit.commit.author.name,
                    commit_time_string
                )
                branch_sections.append(section)
            
            if branch_sections:
                branch_content = '\n\n'.join(branch_sections)
                if branch_name in branches_content:
                    branch_content = branch_content + "\n\n" + branches_content[branch_name]
                
                # 브랜치별 섹션을 details로 감싸기
                branch_section = f'''<details>
<summary><h3 style="display: inline;">✨ {branch_name}</h3></summary>

{branch_content}
</details>'''
                result.append(branch_section)
                logger.debug(f"브랜치 '{branch_name}' 섹션 생성됨")
        
        return result 