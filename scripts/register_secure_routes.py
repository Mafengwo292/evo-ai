with open('/root/evo-ai/distributed/public_api.py') as f:
    content = f.read()

old = '''    # 加载 workflow + milestones 路由
    try:
        from distributed.workflow_routes import register_routes as register_workflow_routes
        register_workflow_routes(app)
        print("[Workflow] Routes registered: /workflow, /milestones, /api/workflow/status")
    except Exception as e:
        print(f"[Workflow] Failed to register: {e}")

    # 启动后台爬虫'''

new = '''    # 加载 workflow + milestones 路由
    try:
        from distributed.workflow_routes import register_routes as register_workflow_routes
        register_workflow_routes(app)
        print("[Workflow] Routes registered: /workflow, /milestones, /api/workflow/status")
    except Exception as e:
        print(f"[Workflow] Failed to register: {e}")

    # 加载 secure vault routes
    try:
        from distributed.secure_routes import register_routes as register_secure_routes
        register_secure_routes(app)
        print("[Secure] Routes registered: /secure (encrypted core data)")
    except Exception as e:
        print(f"[Secure] Failed to register: {e}")

    # 加载 activity routes (实时可视化)
    try:
        from distributed.activity_routes import register_routes as register_activity_routes
        register_activity_routes(app)
        print("[Activity] Routes registered: /agent-activity (real-time visualization)")
    except Exception as e:
        print(f"[Activity] Failed to register: {e}")

    # 启动后台爬虫'''

if old in content:
    content = content.replace(old, new)
    with open('/root/evo-ai/distributed/public_api.py', 'w') as f:
        f.write(content)
    print('Updated public_api.py')
else:
    print('Pattern not found')

import py_compile
try:
    py_compile.compile('/root/evo-ai/distributed/public_api.py', doraise=True)
    print('Syntax OK')
except Exception as e:
    print(f'Syntax error: {e}')