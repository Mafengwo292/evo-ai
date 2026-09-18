#!/usr/bin/env python3
"""
secure_routes.py - 加密核心数据访问
- /secure - 密码 + 通行证 解密
- 提供 SDK / whitepaper / bank info (after auth)
"""

import os, json, base64, hashlib, time
from flask import request, jsonify, send_file, redirect, session
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

VAULT = '/root/evo-ai/data/vault'

PASSWORD = 'Hu8384jian051'

# Load salt + access token
with open(VAULT + '/master.json') as f:
    MASTER = json.load(f)
SALT = base64.b64decode(MASTER['salt_b64'])
with open(VAULT + '/access_token.json') as f:
    TOKEN_DATA = json.load(f)
ACCESS_TOKEN = TOKEN_DATA['token']


def get_fernet(password):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=200000)
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return Fernet(key)


def auth_check(password=None, token=None):
    if token and token == ACCESS_TOKEN:
        return True
    if password == PASSWORD:
        return True
    return False


def decrypt_file(name):
    path = VAULT + '/encrypted/' + name
    if not os.path.exists(path):
        return None
    f = get_fernet(PASSWORD)
    with open(path, 'rb') as fh:
        encrypted = fh.read()
    return f.decrypt(encrypted).decode()


def render_login_page(error=None):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>EVO-AI Secure Vault - Authentication Required</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{ font-family: -apple-system, sans-serif; background: #0a0e1a; color: #c5cdd9; max-width: 500px; margin: 100px auto; padding: 20px; }}
h1 {{ color: #00ff88; text-align: center; }}
.box {{ background: #11151f; padding: 24px; border-radius: 8px; border: 1px solid #2a3142; }}
input {{ width: 100%; padding: 10px; margin: 6px 0; background: #0a0e1a; color: #c5cdd9; border: 1px solid #2a3142; border-radius: 4px; box-sizing: border-box; }}
button {{ width: 100%; padding: 12px; background: #00ff88; color: #0a0e1a; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; margin-top: 12px; }}
.error {{ color: #ff6b6b; padding: 8px; margin: 8px 0; background: #2a1f1f; border-radius: 4px; }}
.success {{ color: #00ff88; padding: 8px; margin: 8px 0; background: #1a2f1a; border-radius: 4px; }}
</style>
</head>
<body>
<h1>🔐 EVO-AI Secure Vault</h1>
<div class="box">
<p style="text-align: center; color: #888;">Authentication required to access encrypted core data.</p>
{('<div class="error">' + error + '</div>') if error else ''}
<form method="POST">
<input type="password" name="password" placeholder="Master password" required>
<button type="submit">Unlock</button>
</form>
<p style="text-align: center; font-size: 0.8em; color: #888; margin-top: 16px;">
Or use access token in URL: <code>/secure?t=TOKEN</code>
</p>
</div>
</body>
</html>""", 200


def render_vault_page():
    """Show all encrypted core data"""
    files_html = ''
    for f in MASTER['files']:
        basename = os.path.basename(f['original'])
        files_html += f'''
<div class="file">
<h3>{basename}</h3>
<p>Encrypted: {f['size_encrypted']} bytes | Original: {f['size_original']} bytes</p>
<a href="/secure/file?name={basename}">View decrypted</a> | <a href="/secure/raw?name={basename}">Raw</a>
</div>
'''

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>EVO-AI Secure Vault</title>
<meta http-equiv="refresh" content="60">
<style>
body {{ font-family: -apple-system, sans-serif; background: #0a0e1a; color: #c5cdd9; max-width: 900px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #00ff88; }}
.box {{ background: #11151f; padding: 20px; border-radius: 8px; margin: 16px 0; border: 1px solid #2a3142; }}
.file {{ background: #0a0e1a; padding: 16px; margin: 12px 0; border-radius: 6px; border-left: 3px solid #00ff88; }}
.file h3 {{ margin: 0 0 8px 0; color: #00ddff; }}
a {{ color: #00ff88; }}
.token {{ background: #1a2f1a; padding: 8px; border-radius: 4px; font-family: monospace; word-break: break-all; color: #00ff88; margin: 12px 0; }}
.bank {{ background: #2a1f1f; padding: 12px; border-radius: 4px; margin: 8px 0; font-family: monospace; }}
pre {{ background: #0a0e1a; padding: 12px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; }}
</style>
</head>
<body>
<h1>🔐 EVO-AI Secure Vault (UNLOCKED)</h1>
<div class="box">
<h2>🏦 Bank Account (Donation)</h2>
<div class="bank">
中国邮政储蓄银行 (China Postal Savings Bank)<br>
Account: 6221804230000091592<br>
Name: 胡建<br>
Branch: 萍乡市长兴北路营业所<br>
SWIFT: PSBCCNBJ
</div>
</div>

<div class="box">
<h2>📜 Encrypted Core Files</h2>
{files_html}
</div>

<div class="box">
<h2>🔑 Access Token</h2>
<p>Use this token to access /secure from anywhere:</p>
<div class="token">{ACCESS_TOKEN}</div>
<p>Expires: {time.ctime(TOKEN_DATA['expires'])}</p>
<p>Usage: <code>curl "http://47.253.174.153:80/secure?t={ACCESS_TOKEN}"</code></p>
</div>

<p><a href="/dashboard">📊 Dashboard</a> | <a href="/">🏠 Home</a></p>
</body>
</html>""", 200


def render_file(name):
    """Render decrypted file"""
    content = decrypt_file(name)
    if content is None:
        return '<h1>File not found</h1>', 404
    # escape for HTML
    import html as h
    safe = h.escape(content)
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{name} - Secure Vault</title>
<style>body {{ font-family: monospace; background: #0a0e1a; color: #c5cdd9; padding: 20px; }}
h1 {{ color: #00ff88; }}
pre {{ background: #11151f; padding: 16px; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; }}
a {{ color: #00ddff; }}
</style></head><body>
<h1>{name}</h1>
<pre>{safe}</pre>
<p><a href="/secure">← Back to vault</a></p>
</body></html>""", 200


def register_routes(app):
    @app.route("/secure", methods=["GET", "POST"])
    def secure():
        # Check query string token first
        token = request.args.get('t')
        if auth_check(token=token):
            return render_vault_page()

        # POST: password
        if request.method == 'POST':
            pwd = request.form.get('password', '')
            if auth_check(password=pwd):
                return render_vault_page()
            return render_login_page('Invalid password')

        return render_login_page()

    @app.route("/secure/file")
    def secure_file():
        token = request.args.get('t')
        if not auth_check(token=token):
            return redirect('/secure')
        name = request.args.get('name', '')
        return render_file(name)

    @app.route("/secure/raw")
    def secure_raw():
        token = request.args.get('t')
        if not auth_check(token=token):
            return 'Auth required', 401
        name = request.args.get('name', '')
        content = decrypt_file(name)
        if content is None:
            return 'Not found', 404
        return content, 200, {'Content-Type': 'text/plain'}


if __name__ == '__main__':
    print('Secure Vault Module')
    print(f'Vault: {VAULT}')
    print(f'Access token: {ACCESS_TOKEN}')