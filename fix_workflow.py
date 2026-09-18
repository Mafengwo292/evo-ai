import re

with open('/root/evo-ai/distributed/public_api.py') as f:
    content = f.read()

# 修 syntax error - 找正确的 print 行
old = 'print([Workflow] Routes registered: /workflow, /milestones, /api/workflow/status")'
new = 'print("[Workflow] Routes registered: /workflow, /milestones, /api/workflow/status")'

if old in content:
    content = content.replace(old, new)
    print('Fixed syntax error')
else:
    print('Pattern not found, trying alternative fix')

# Save
with open('/root/evo-ai/distributed/public_api.py', 'w') as f:
    f.write(content)

# Syntax check
import py_compile
try:
    py_compile.compile('/root/evo-ai/distributed/public_api.py', doraise=True)
    print('Syntax OK')
except Exception as e:
    print(f'Syntax error: {e}')