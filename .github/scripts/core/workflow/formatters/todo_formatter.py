"""
TODO 섹션 포맷팅을 담당하는 모듈
"""
from typing import List, Tuple

def create_todo_section(todos: List[Tuple[bool, str]]) -> str:
    """TODO 섹션을 생성합니다."""
    if not todos:
        return ''
        
    sections = {}
    category_order = []
    current_category = 'General'
    
    for checked, text in todos:
        if text.startswith('@'):
            current_category = text[1:].strip()
            if current_category not in category_order:
                category_order.append(current_category)
            continue
            
        if current_category not in sections:
            sections[current_category] = []
        sections[current_category].append((checked, text))
    
    if not category_order:
        category_order.append('General')
    
    result = []
    for category in category_order:
        if category not in sections:
            continue
            
        items = sections[category]
        completed = sum(1 for checked, _ in items if checked)
        section = f'''<details>
<summary><h3 style="display: inline;">📑 {category} ({completed}/{len(items)})</h3></summary>

{'\n'.join(f"- [{'x' if checked else ' '}] {text}" for checked, text in items)}

⚫
</details>'''
        result.append(section)
    
    return '\n\n'.join(result)

class TodoFormatter:
    @staticmethod
    def create_todo_section(todos: List[Tuple[bool, str]]) -> str:
        """TODO 섹션을 생성합니다."""
        return create_todo_section(todos) 