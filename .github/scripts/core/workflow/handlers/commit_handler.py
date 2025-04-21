"""
커밋 처리를 담당하는 핸들러
"""
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from github.Repository import Repository
import pytz
from ...workflow.models.commit import parse_commit_message, is_merge_commit_message
from ..utils.logger import logger
from ..utils.github_utils import retry_api_call

class CommitProcessor:
    def __init__(self, repo: Repository, timezone: str):
        self.repo = repo
        self.timezone = timezone
        self.tz = pytz.timezone(timezone)
        self.today = datetime.now(self.tz).date()
        self.commit_history = {}
        self.author_branches = {}
    
    def get_commit_key(self, commit) -> Tuple[str, str, str]:
        """커밋의 고유 키를 생성합니다."""
        return (
            commit.commit.message.strip(),
            commit.commit.author.name,
            commit.commit.author.date.strftime('%H:%M:%S')
        )
    
    def get_author_branch(self, author_name: str) -> str:
        """작성자의 가상 브랜치 이름을 반환합니다."""
        if author_name not in self.author_branches:
            self.author_branches[author_name] = f"Author_{author_name}"
        return self.author_branches[author_name]
    
    def process_commit(self, commit, branch_name: str) -> bool:
        """단일 커밋을 처리하고 유효성을 반환합니다."""
        if is_merge_commit_message(commit.commit.message):
            logger.debug(f"머지 커밋 무시: [{commit.sha[:7]}]")
            return False
            
        commit_key = self.get_commit_key(commit)
        if commit_key in self.commit_history:
            original_branch, _ = self.commit_history[commit_key]
            logger.debug(f"중복 커밋 무시: [{commit.sha[:7]}] - 원본 브랜치: {original_branch}")
            return False
            
        # 작성자의 가상 브랜치로 매핑
        author_name = commit.commit.author.name
        author_branch = self.get_author_branch(author_name)
        self.commit_history[commit_key] = (author_branch, commit)
        logger.debug(f"커밋 추가: [{commit.sha[:7]}] by {author_name}")
        return True

    def get_todays_commits(self) -> Dict[str, List]:
        """오늘의 커밋을 작성자별로 가져옵니다."""
        logger.section("Getting Today's Unique Commits by Authors")
        author_commits = {}
        processed_shas = set()
        
        try:
            branches = list(self.repo.get_branches())
            logger.debug(f"총 {len(branches)}개의 브랜치 발견")
            
            branches.sort(
                key=lambda b: self.repo.get_commit(b.commit.sha).commit.author.date,
                reverse=True
            )
            
            for branch in branches:
                branch_name = branch.name
                latest_commit = self.repo.get_commit(branch.commit.sha)
                latest_date = latest_commit.commit.author.date.replace(tzinfo=pytz.UTC).astimezone(self.tz).date()
                
                if latest_date < self.today:
                    logger.debug(f"브랜치 {branch_name}의 최신 커밋이 오늘 이전입니다. 나머지 브랜치 검사 중단")
                    break
                
                logger.debug(f"\n브랜치 확인 중: {branch_name}")
                try:
                    commits = self.repo.get_commits(sha=branch.commit.sha)
                    
                    for commit in commits:
                        commit_date = commit.commit.author.date.replace(tzinfo=pytz.UTC).astimezone(self.tz).date()
                        
                        # 오늘 날짜가 아니면 다음 브랜치로
                        if commit_date != self.today:
                            if commit_date < self.today:
                                break
                            continue
                        
                        # 이미 처리된 SHA면 건너뜁니다
                        if commit.sha in processed_shas:
                            continue
                        
                        # 머지 커밋이거나 머지 결과물이면 건너뜁니다
                        if is_merge_commit_message(commit.commit.message) or len(commit.parents) > 1:
                            continue
                        
                        # 작성자 정보 확인
                        author_name = commit.commit.author.name
                        author_branch = self.get_author_branch(author_name)
                        
                        # 유효한 커밋이면 추가
                        if self.process_commit(commit, branch_name):
                            if author_branch not in author_commits:
                                author_commits[author_branch] = []
                            author_commits[author_branch].append(commit)
                            processed_shas.add(commit.sha)
                    
                except Exception as e:
                    logger.error(f"{branch_name} 브랜치 처리 중 오류 발생: {str(e)}")
                    continue
            
            # 작성자별 커밋 통계
            total_commits = sum(len(commits) for commits in author_commits.values())
            logger.debug(f"\n총 {len(author_commits)}명의 작성자, {total_commits}개의 고유 커밋 발견")
            
            for author_branch, commits in author_commits.items():
                author_name = author_branch.replace("Author_", "")
                logger.debug(f"{author_name}: {len(commits)}개의 커밋")
            
            return author_commits
            
        except Exception as e:
            logger.error(f"브랜치 목록 가져오기 실패: {str(e)}")
            return {} 