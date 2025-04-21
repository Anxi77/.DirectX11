"""
DSR(Daily Status Report) 보고서 포맷팅을 담당하는 모듈
"""
from typing import List
from ..formatters.todo_formatter import TodoFormatter
from ..utils.date_utils import format_issue_title

class DSRFormatter:
    def __init__(self, project_name: str, date_string: str):
        self.project_name = project_name
        self.date_string = date_string
        self.todo_formatter = TodoFormatter()
    
    def create_report(self, branches_content: List[str], todos: List) -> str:
        """전체 DSR 보고서를 생성합니다."""
        title = format_issue_title(self.date_string, self.project_name)
        
        return f'''# {title}

<div align="center">

## 📊 Branch Summary

</div>

{"\n\n".join(branches_content)}

<div align="center">

## 📝 Todo

{self.todo_formatter.create_todo_section(todos)}''' 