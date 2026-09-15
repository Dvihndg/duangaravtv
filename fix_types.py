from typing import Optional
import os

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    modified = False

    # Fix datetime.utcnow
    if 'datetime.utcnow' in content:
        if 'models.py' in filepath:
            if 'def get_utc_now()' not in content:
                content = content.replace('from datetime import datetime', 'from datetime import datetime, timezone\n\ndef get_utc_now():\n    return datetime.now(timezone.utc)\n')
            content = content.replace('datetime.utcnow', 'get_utc_now')
        else:
            if 'from datetime import datetime' in content and 'timezone' not in content:
                content = content.replace('from datetime import datetime', 'from datetime import datetime, timezone')
            if 'datetime.datetime.utcnow' in content:
                 content = content.replace('datetime.datetime.utcnow()', 'datetime.now(timezone.utc)')
                 content = content.replace('datetime.datetime.utcnow', 'datetime.now(timezone.utc)')
            content = content.replace('datetime.utcnow()', 'datetime.now(timezone.utc)')
            content = content.replace('datetime.utcnow', 'datetime.now(timezone.utc)')
        modified = True
        
    # Fix Default None is not assignable to parameter with type str/int
    # Example: api_key: str = None -> api_key: Optional[str] = None
    import re
    # Match patterns like: var: str = None
    new_content = re.sub(r'(\w+):\s*(str|int|float|bool|type\[BaseModel\])\s*=\s*None', r'\1: \2 | None = None', content)
    if new_content != content:
        content = new_content
        modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {filepath}")

for root, dirs, files in os.walk('backend'):
    for file in files:
        if file.endswith('.py'):
            process_file(os.path.join(root, file))
