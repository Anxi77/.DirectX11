"""
커밋 메시지 처리를 위한 유틸리티 함수들
"""
import re
from typing import Dict, Optional

COMMIT_TYPES = {
    'feat': {'emoji': '✨', 'label': 'feature', 'description': 'New Feature'},
    'fix': {'emoji': '🐛', 'label': 'bug', 'description': 'Bug Fix'},
    'refactor': {'emoji': '♻️', 'label': 'refactor', 'description': 'Code Refactoring'},
    'docs': {'emoji': '📝', 'label': 'documentation', 'description': 'Documentation Update'},
    'test': {'emoji': '✅', 'label': 'test', 'description': 'Test Update'},
    'chore': {'emoji': '🔧', 'label': 'chore', 'description': 'Build/Config Update'},
    'style': {'emoji': '💄', 'label': 'style', 'description': 'Code Style Update'},
    'perf': {'emoji': '⚡️', 'label': 'performance', 'description': 'Performance Improvement'},
}

class CommitMessage:
    def __init__(self, type_: str, title: str, body: str = '', todo: str = '', footer: str = ''):
        self.type = type_
        self.title = title
        self.body = body
        self.todo = todo
        self.footer = footer
        self.type_info = COMMIT_TYPES.get(type_.lower(), {'emoji': '🔍', 'label': 'other', 'description': 'Other'})

    @classmethod
    def parse(cls, message: str) -> Optional['CommitMessage']:
        sections = {'title': '', 'body': '', 'todo': '', 'footer': ''}
        current_section = 'title'

        message_lines = message.split('\n')
        if not message_lines:
            return None
            
        sections['title'] = message_lines[0].strip()
        
        for line in message_lines[1:]:
            line = line.strip()
            if not line:
                continue

            if line.lower() in ['[body]', '[todo]', '[footer]']:
                current_section = line.strip('[]').lower()
                continue
            
            if current_section in sections:
                if sections[current_section]:
                    sections[current_section] += '\n'
                sections[current_section] += line

        title_match = re.match(r'\[(.*?)\]\s*(.*)', sections['title'])
        if not title_match:
            return None

        return cls(
            type_=title_match.group(1),
            title=title_match.group(2),
            body=sections['body'],
            todo=sections['todo'],
            footer=sections['footer']
        )

def parse_commit_message(message: str) -> Optional[Dict]:
    """커밋 메시지를 파싱합니다."""
    commit = CommitMessage.parse(message)
    if not commit:
        return None

    return {
        'type': commit.type,
        'type_info': commit.type_info,
        'title': commit.title,
        'body': commit.body,
        'todo': commit.todo,
        'footer': commit.footer
    }

def is_merge_commit_message(message: str) -> bool:
    """머지 커밋 메시지인지 확인합니다."""
    message = message.lower().strip()
    return message.startswith('merge') or 'merge branch' in message or 'merge pull request' in message 