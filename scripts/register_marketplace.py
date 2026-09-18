with open('/root/evo-ai/distributed/public_api.py') as f:
    content = f.read()

old = '''    # 启动后台爬虫'''

new = '''    # 加载 marketplace (让 agents 赚 EVO)
    try:
        from distributed.marketplace_routes import register_routes as register_marketplace_routes
        register_marketplace_routes(app)
        print("[Marketplace] Routes registered: /marketplace, /api/market/*")
    except Exception as e:
        print(f"[Marketplace] Failed to register: {e}")

    # 启动后台爬虫'''

if old in content:
    content = content.replace(old, new)
    with open('/root/evo-ai/distributed/public_api.py', 'w') as f:
        f.write(content)
    print('Updated public_api.py')
else:
    print('Pattern not found')

import py_compile
py_compile.compile('/root/evo-ai/distributed/public_api.py', doraise=True)
print('Syntax OK')