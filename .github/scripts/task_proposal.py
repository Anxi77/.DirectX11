import os
from github import Github
from pathlib import Path
import re
import csv
from io import StringIO
import json
from datetime import datetime

def parse_csv_section(section_content):
    """CSV 섹션 내용을 파싱합니다."""
    if not section_content.strip():
        return []
    
    result = []
    # 개행 문자 정규화
    section_content = section_content.replace('\r\n', '\n')
    
    # 연속된 빈 줄 제거
    lines = [line for line in section_content.split('\n') if line.strip()]
    
    for line in lines:
        # StringIO를 사용하여 CSV 파싱
        f = StringIO(line)
        reader = csv.reader(f, skipinitialspace=True)
        row = next(reader, None)
        
        if row:
            # 빈 필드 제거 및 공백 정리
            cleaned_row = []
            for field in row:
                field = field.strip()
                if field:  # 빈 필드가 아닌 경우만 추가
                    # 따옴표 제거 (시작과 끝에 있는 경우만)
                    if field.startswith('"') and field.endswith('"'):
                        field = field[1:-1]
                    cleaned_row.append(field)
            
            if cleaned_row:  # 비어있지 않은 행만 추가
                result.append(cleaned_row)
    
    return result

def convert_schedule_to_mermaid(schedule_data):
    """일정계획 데이터를 Mermaid 간트 차트 형식으로 변환합니다."""
    tasks = []
    for item in schedule_data:
        task = item['task']
        date = item['date']
        duration = item['duration']
        tasks.append(f"    {task} :{date}, {duration}")
    return '\n'.join(tasks)

def read_csv_data(file_path):
    """CSV 파일에서 태스크 데이터를 읽어옵니다."""
    data = {}
    current_section = None
    section_content = ""
    
    # 인코딩 시도 순서 수정
    encodings = ['euc-kr', 'utf-8', 'cp949']
    
    for encoding in encodings:
        try:
            print(f"\n=== CSV 파일 읽기 시도 ({encoding}) ===")
            print(f"파일 경로: {file_path}")
            
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                
            # 파일 내용이 비어있는지 확인
            if not content.strip():
                print("파일이 비어있습니다")
                continue
                
            print(f"파일 읽기 성공 (인코딩: {encoding})")
            print(f"파일 내용 미리보기:\n{content[:200]}...")  # 디버깅용
            
            lines = content.split('\n')
            
            # 기본 정보 처리
            for line in lines:
                line = line.strip()
                if not line:  # 빈 줄 건너뛰기
                    continue
                    
                # 섹션 시작 확인
                if line.startswith('[') and ']' in line:
                    # 이전 섹션 처리
                    if current_section == '[태스크명]' and section_content:
                        # 태스크명 섹션의 내용 처리
                        content_lines = section_content.strip().split('\n')
                        for content_line in content_lines:
                            parts = [p.strip() for p in content_line.split(',') if p.strip()]
                            if len(parts) >= 2:
                                key = parts[0]
                                value = parts[1]
                                if key == '태스크명':
                                    data[current_section] = value
                                elif not key.startswith('['):  # 기본 정보 필드
                                    data[key] = value
                    
                    # 새로운 섹션 시작
                    section_name = line.split(',')[0]
                    current_section = section_name
                    section_content = ""
                    
                    # 태스크명이 섹션 시작 라인에 있는 경우 처리
                    if section_name == '[태스크명]':
                        parts = [p.strip() for p in line.split(',') if p.strip()]
                        if len(parts) >= 2:
                            data[section_name] = parts[1]
                    continue
                
                # 섹션 내용 수집
                if current_section:
                    section_content += line + "\n"
                    
                    # 태스크 목적
                    if current_section == '[태스크목적]':
                        text = line.split(',')[0].strip()
                        if text and not text.startswith('['):
                            data[current_section] = text
                    
                    # 태스크 범위
                    elif current_section == '[태스크범위]':
                        parts = [p.strip() for p in line.split(',') if p.strip()]
                        if parts and not any(p.startswith('[') for p in parts):
                            if current_section not in data:
                                data[current_section] = []
                            data[current_section].extend(parts)
                    
                    # 필수/선택 요구사항
                    elif current_section in ['[필수요구사항]', '[선택요구사항]']:
                        parts = [p.strip() for p in line.split(',') if p.strip()]
                        if parts and not any(p.startswith('[') for p in parts):
                            if current_section not in data:
                                data[current_section] = []
                            data[current_section].extend(parts)
                    
                    # 일정계획
                    elif current_section == '[일정계획]':
                        parts = [p.strip() for p in line.split(',') if p.strip()]
                        if len(parts) >= 3 and not any(p.startswith('[') for p in parts):
                            if current_section not in data:
                                data[current_section] = []
                            data[current_section].append({
                                'task': parts[0],
                                'date': parts[1],
                                'duration': parts[2]
                            })
            
            # 마지막 섹션 처리
            if current_section == '[태스크명]' and section_content:
                content_lines = section_content.strip().split('\n')
                for line in content_lines:
                    parts = [p.strip() for p in line.split(',') if p.strip()]
                    if len(parts) >= 2:
                        key = parts[0]
                        value = parts[1]
                        if key == '태스크명':
                            data[current_section] = value
                        elif not key.startswith('['):  # 기본 정보 필드
                            data[key] = value
            
            # 데이터 후처리
            for key in data:
                if isinstance(data[key], list):
                    if key == '[일정계획]':
                        # 일정계획은 그대로 둠
                        pass
                    else:
                        # 리스트 항목들을 문자열로 변환
                        data[key] = '\n'.join(f"- {item}" for item in data[key])
            
            if data:  # 데이터가 성공적으로 파싱된 경우
                print(f"\n총 {len(data)}개의 항목을 읽었습니다.")
                print("\n=== 파싱된 데이터 ===")
                for key, value in data.items():
                    print(f"\n{key}:")
                    print(value)
                    print("-" * 50)
                return data
            
            print("\n데이터가 비어있습니다!")
            print(f"현재 데이터 상태: {data}")
            continue  # 다음 인코딩으로 시도
            
        except UnicodeDecodeError:
            print(f"{encoding} 인코딩으로 읽기 실패")
            continue
        except Exception as e:
            print(f"파일 처리 중 오류 발생: {str(e)}")
            continue
    
    raise ValueError("파일을 읽을 수 없거나 데이터가 없습니다.")

def create_issue_body(data, project_name):
    """이슈 본문을 생성합니다."""
    try:
        # 일정계획 섹션이 없거나 비어있으면 기본값 사용
        schedule_data = data.get('[일정계획]', [])
        if not schedule_data or len(schedule_data) == 0:
            schedule_mermaid = """```mermaid
gantt
    title 일정 계획
    dateFormat  YYYY-MM-DD
    section 기본 일정
    일정 미정     :2025-02-21, 1d
```"""
        else:
            schedule_mermaid = convert_schedule_to_mermaid(schedule_data)

        # 나머지 섹션들도 비어있을 경우 처리
        task_purpose = data.get('[태스크목적]', '(목적 미정)')
        task_scope = format_list_items(data.get('[태스크범위]', ['(범위 미정)']))
        required = format_list_items(data.get('[필수요구사항]', ['(필수요구사항 미정)']))
        optional = format_list_items(data.get('[선택요구사항]', ['(선택요구사항 미정)']))

        # 기본 정보도 없을 경우 처리
        proposer = data.get('제안자', '미정')
        proposal_date = data.get('제안일', datetime.now().strftime('%Y-%m-%d'))
        target_date = data.get('구현목표일', '미정')

        return f"""# {project_name} 태스크 제안서

## 📋 기본 정보
- 제안자: {proposer}
- 제안일: {proposal_date}
- 구현목표일: {target_date}

## 🎯 태스크 목적
{task_purpose}

## 📝 태스크 범위
{task_scope}

## ✅ 필수 요구사항
{required}

## 💭 선택 요구사항
{optional}

## 📅 일정 계획
{schedule_mermaid}
"""
    except Exception as e:
        print(f"이슈 본문 생성 중 오류 발생: {str(e)}")
        # 최소한의 정보로 이슈 생성
        return f"""# {project_name} 태스크 제안서

## ⚠️ 주의
원본 태스크 제안서 처리 중 오류가 발생했습니다.
CSV 파일의 형식을 확인해주세요.

## 📋 원본 데이터
```
{json.dumps(data, indent=2, ensure_ascii=False)}
```
"""

def sanitize_project_name(name):
    """프로젝트 이름에서 특수문자를 제거하고 적절한 형식으로 변환합니다."""
    print(f"\n=== 프로젝트 이름 정리 ===")
    print(f"원본 이름: {name}")
    
    # 시작 부분의 . 제거
    while name.startswith('.'):
        name = name[1:]
    
    # 특수문자를 공백으로 변환
    sanitized = re.sub(r'[^\w\s-]', ' ', name)
    
    # 연속된 공백을 하나로 변환하고 앞뒤 공백 제거
    sanitized = ' '.join(sanitized.split())
    
    print(f"변환된 이름: {sanitized}")
    return sanitized

def format_list_items(items):
    """리스트 항목을 마크다운 형식으로 변환합니다."""
    if isinstance(items, str):
        return items
    return '\n'.join(f'- {item}' for item in items)

def main():
    # GitHub 클라이언트 초기화
    github_token = os.getenv('GITHUB_TOKEN')
    github = Github(github_token)
    
    # 저장소 정보 가져오기
    repo_name = os.getenv('GITHUB_REPOSITORY')
    repo = github.get_repo(repo_name)
    project_name = sanitize_project_name(repo.name)  # 리포지토리명 정리
    
    print(f"\n=== 저장소 정보 ===")
    print(f"원본 저장소명: {repo.name}")
    print(f"정리된 프로젝트명: {project_name}")
    
    # CSV 파일 찾기
    csv_dir = Path('TaskProposals')
    print(f"\n=== CSV 파일 검색 ===")
    print(f"검색 디렉토리: {csv_dir.absolute()}")
    
    for csv_file in csv_dir.glob('*.csv'):
        if csv_file.is_file():
            print(f"\n발견된 CSV 파일: {csv_file}")
            # CSV 데이터 읽기
            data = read_csv_data(csv_file)
            
            # 이슈 생성
            issue_title = f"[{project_name}] {data['[태스크명]']}"
            print(f"생성할 이슈 제목: {issue_title}")
            
            issue_body = create_issue_body(data, project_name)
            
            issue = repo.create_issue(
                title=issue_title,
                body=issue_body,
                labels=['⌛ 검토대기']
            )
            print(f"이슈 생성 완료: #{issue.number}")
            
            # 처리된 CSV 파일 이동 또는 삭제
            os.remove(csv_file)
            print(f"CSV 파일 삭제 완료: {csv_file}")

if __name__ == '__main__':
    main() 