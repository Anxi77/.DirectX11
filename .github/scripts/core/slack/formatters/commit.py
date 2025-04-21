"""커밋 메시지 포맷터"""
from typing import Dict, List
from .base import BaseFormatter
import re

COMMIT_TYPES = {
    'feat': {'emoji': '✨', 'label': 'feature', 'description': '새로운 기능'},
    'fix': {'emoji': '🐛', 'label': 'bug', 'description': '버그 수정'},
    'refactor': {'emoji': '♻️', 'label': 'refactor', 'description': '코드 리팩토링'},
    'docs': {'emoji': '📝', 'label': 'documentation', 'description': '문서 수정'},
    'test': {'emoji': '✅', 'label': 'test', 'description': '테스트 추가/수정'},
    'chore': {'emoji': '🔧', 'label': 'chore', 'description': '빌드/설정 변경'},
    'style': {'emoji': '💄', 'label': 'style', 'description': '코드 스타일 변경'},
    'perf': {'emoji': '⚡️', 'label': 'performance', 'description': '성능 개선'},
}

class CommitFormatter(BaseFormatter):
    """커밋 메시지 포맷팅"""
    
    @staticmethod
    def parse_commit_message(message: str) -> Dict:
        """커밋 메시지 파싱"""
        # [type] message 형식 파싱
        title_match = re.match(r'\[(.*?)\]\s*(.*)', message.split('\n')[0])
        if not title_match:
            return {
                'type': 'other',
                'type_info': {'emoji': '🔍', 'label': 'other', 'description': '기타'},
                'title': message.split('\n')[0],
                'body': '\n'.join(message.split('\n')[1:]).strip()
            }
            
        commit_type = title_match.group(1).lower()
        title = title_match.group(2)
        
        type_info = COMMIT_TYPES.get(commit_type, {'emoji': '🔍', 'label': 'other', 'description': '기타'})
        
        # 본문과 메타데이터 분리
        parts = message.split('\n')
        body = []
        current_section = 'body'
        
        for line in parts[1:]:
            line = line.strip()
            if not line:
                continue
                
            if line.lower() in ['[body]', '[todo]', '[footer]']:
                current_section = line.strip('[]').lower()
                continue
                
            if current_section == 'body':
                body.append(line)
        
        return {
            'type': commit_type,
            'type_info': type_info,
            'title': title,
            'body': '\n'.join(body)
        }
    
    @classmethod
    def format_commits(cls, commits: List[Dict], repository: str, branch: str) -> Dict:
        """커밋 메시지 포맷팅"""
        blocks = [
            cls.create_header(f"🔄 새로운 커밋이 푸시되었습니다"),
            cls.create_section(fields=[
                {"type": "mrkdwn", "text": f"*저장소:*\n{repository}"},
                {"type": "mrkdwn", "text": f"*브랜치:*\n{branch}"}
            ])
        ]
        
        for commit in commits[:5]:  # 최근 5개 커밋만 표시
            author = commit.get('author', {}).get('name', 'Unknown')
            parsed = cls.parse_commit_message(commit.get('message', ''))
            url = commit.get('url', '')
            
            commit_block = cls.create_section(
                text=f"{parsed['type_info']['emoji']} *{author}* - {parsed['type_info']['description']}\n"
                     f"*{parsed['title']}*\n"
                     f"{cls._format_body(parsed['body'])}\n"
                     f"<{url}|커밋 보기>"
            )
            blocks.append(commit_block)
        
        if len(commits) > 5:
            blocks.append(cls.create_section(
                text=f"_이외 {len(commits) - 5}개의 커밋이 더 있습니다._"
            ))
        
        blocks.append(cls.create_divider())
        return {"blocks": blocks}
    
    @staticmethod
    def _format_body(body: str) -> str:
        """커밋 본문을 포맷팅"""
        if not body:
            return ''
            
        lines = []
        for line in body.strip().split('\n'):
            line = line.strip()
            if line:
                if line.startswith('-'):
                    line = line[1:].strip()
                lines.append(f"• {line}")
        
        return '\n'.join(lines) 