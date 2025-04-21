"""
태스크 제안서 추적 및 승인 처리를 담당하는 모듈
"""
import os
import re
from github import Github
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

PROPOSAL_LABELS = {
    'pending': '⌛ 검토대기',
    'hold': '⏸️ 보류',
    'approved': '✅ 승인완료',
    'rejected': '❌ 반려'
}

class TaskProposalTracker:
    def __init__(self, token: str):
        self.g = Github(token)
        self.repo = self.g.get_repo(os.environ.get('GITHUB_REPOSITORY'))
    
    def process_proposals(self):
        """승인된 제안서를 처리합니다."""
        logger.info("태스크 제안서 처리 시작")
        
        for issue in self.repo.get_issues(state='open'):
            labels = [label.name for label in issue.labels]
            
            # 검토대기 라벨이 있고, 승인완료 라벨이 추가된 이슈만 처리
            if PROPOSAL_LABELS['pending'] in labels and PROPOSAL_LABELS['approved'] in labels:
                try:
                    self._convert_to_task(issue)
                    issue.create_comment(
                        f"✅ 제안서가 승인되어 태스크로 변환되었습니다.\n"
                        f"태스크 링크: #{issue.number}"
                    )
                    logger.info(f"제안서 #{issue.number} 처리 완료")
                except Exception as e:
                    logger.error(f"제안서 #{issue.number} 처리 중 오류 발생: {str(e)}")
                    # 오류 발생 시 코멘트 추가
                    issue.create_comment(
                        f"⚠️ 태스크 변환 중 오류가 발생했습니다:\n```\n{str(e)}\n```"
                    )
    
    def _convert_to_task(self, proposal):
        """승인된 제안서를 태스크로 변환합니다."""
        # 제안서 제목에서 프로젝트명과 태스크명 추출
        match = re.match(r'\[(.*?)\] (.+)$', proposal.title)
        if not match:
            raise ValueError("제안서 제목 형식이 올바르지 않습니다.")
        
        project_name, task_name = match.groups()
        
        # 제안서 본문에서 정보 추출
        info = self._parse_proposal_body(proposal.body)
        
        # 태스크 이슈 생성
        task_body = self._create_task_body(info)
        task_title = f"[{project_name}] {task_name}"
        
        # 태스크 라벨 설정
        labels = ['category:기능 개발']  # 기본 카테고리
        if info.get('구현목표일'):
            days = self._calculate_days(info['구현목표일'])
            labels.append(f"weight:{days}")
        
        # 태스크 이슈 생성
        task_issue = self.repo.create_issue(
            title=task_title,
            body=task_body,
            labels=labels,
            assignees=[info.get('제안자', '').split('@')[-1]]  # @ 이후 부분만 사용
        )
        
        # 제안서에 태스크 링크 추가
        proposal.create_comment(
            f"✅ 제안서가 승인되어 태스크로 변환되었습니다.\n"
            f"태스크 링크: #{task_issue.number}"
        )
    
    def _parse_proposal_body(self, body: str) -> dict:
        """제안서 본문에서 필요한 정보를 추출합니다."""
        info = {}
        lines = body.split('\n')
        current_section = None
        current_subsection = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 섹션 확인
            if line.startswith('## '):
                current_section = line[3:].strip()
                current_subsection = None
                continue
            
            # 서브섹션 확인
            if line.startswith('### '):
                current_subsection = line[4:].strip()
                continue
            
            # 기본 정보 파싱
            if current_section == "📋 기본 정보":
                if line.startswith('- '):
                    key, value = line[2:].split(':', 1)
                    info[key.strip()] = value.strip()
            
            # 태스크 목적 파싱
            elif current_section == "🎯 태스크 목적":
                if not line.startswith('#'):
                    info['purpose'] = line
            
            # 태스크 범위 파싱
            elif current_section == "📝 태스크 범위":
                if 'scope' not in info:
                    info['scope'] = []
                if line.startswith('- '):
                    info['scope'].append(line[2:])
            
            # 필수 요구사항 파싱
            elif current_section == "✅ 필수 요구사항":
                if 'requirements' not in info:
                    info['requirements'] = {}
                if current_subsection:
                    if current_subsection not in info['requirements']:
                        info['requirements'][current_subsection] = []
                    if line.startswith('- '):
                        info['requirements'][current_subsection].append(line[2:])
        
        return info
    
    def _calculate_days(self, target_date: str) -> str:
        """목표일까지의 기간을 계산합니다."""
        try:
            target = datetime.strptime(target_date, '%Y-%m-%d')
            start = datetime.strptime('2025-02-21', '%Y-%m-%d')
            days = (target - start).days
            return f"{days}d" if days > 0 else "1d"
        except:
            return "14d"  # 기본값
    
    def _create_task_body(self, info: dict) -> str:
        """태스크 이슈 본문을 생성합니다."""
        # 기본 정보 포맷팅
        basic_info = f"""## 📋 태스크 정보
- 제안자: {info.get('제안자', '미지정')}
- 제안일: {info.get('제안일', '미지정')}
- 구현목표일: {info.get('구현목표일', '미지정')}
"""

        # 목적 포맷팅
        purpose = f"""## 🎯 태스크 목적
{info.get('purpose', '목적이 지정되지 않았습니다.')}
"""

        # 범위 포맷팅
        scope = "## 📝 태스크 범위\n"
        for item in info.get('scope', []):
            scope += f"- {item}\n"

        # 요구사항 포맷팅
        requirements = "## ✅ 요구사항\n"
        for section, items in info.get('requirements', {}).items():
            requirements += f"\n### {section}\n"
            for item in items:
                requirements += f"- [ ] {item}\n"

        return f"""{basic_info}
{purpose}
{scope}
{requirements}
## 📝 참고사항
- 이 태스크는 승인된 제안서에서 자동으로 생성되었습니다.
"""

def main():
    github_token = os.getenv('GITHUB_TOKEN')
    tracker = TaskProposalTracker(github_token)
    tracker.process_proposals()

if __name__ == '__main__':
    main() 