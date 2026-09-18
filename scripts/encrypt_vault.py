#!/usr/bin/env python3
"""encrypt_vault.py - 加密 EVO-AI 核心数据"""
import os, json, hashlib, base64, time, shutil
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

PASSWORD = 'Hu8384jian051'
SALT = os.urandom(16)

kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=SALT,
    iterations=200000,
)
key = base64.urlsafe_b64encode(kdf.derive(PASSWORD.encode()))
fernet = Fernet(key)

CORE_FILES = [
    '/root/evo-ai/sdk/evo_ai.py',
    '/root/evo-ai/TOKEN_WHITEPAPER.md',
    '/root/evo-ai/PROPOSAL.md',
    '/root/evo-ai/WORKFLOW_24H.md',
    '/root/evo-ai/MILESTONES.md',
    '/root/evo-ai/data/donations.json',
]

VAULT = '/root/evo-ai/data/vault'
os.makedirs(VAULT, exist_ok=True)
os.makedirs(VAULT + '/encrypted', exist_ok=True)

encrypted_log = []
for filepath in CORE_FILES:
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'rb') as f:
        data = f.read()
    encrypted = fernet.encrypt(data)
    enc_path = VAULT + '/encrypted/' + os.path.basename(filepath) + '.enc'
    with open(enc_path, 'wb') as f:
        f.write(encrypted)
    encrypted_log.append({
        'original': filepath,
        'encrypted': enc_path,
        'size_original': len(data),
        'size_encrypted': len(encrypted),
        'timestamp': time.time(),
    })

print('Encrypted ' + str(len(encrypted_log)) + ' files:')
for e in encrypted_log:
    print('  ' + e['original'] + ' -> ' + e['encrypted'])

master = {
    'password_hash': hashlib.sha256(PASSWORD.encode()).hexdigest(),
    'salt_b64': base64.b64encode(SALT).decode(),
    'files': encrypted_log,
    'created': time.time(),
}
with open(VAULT + '/master.json', 'w') as f:
    json.dump(master, f, indent=2)

# Generate permanent access token
ACCESS_TOKEN = base64.urlsafe_b64encode(os.urandom(32)).decode()
TOKEN_EXPIRY = time.time() + 365 * 24 * 3600
TOKEN_FILE = VAULT + '/access_token.json'
with open(TOKEN_FILE, 'w') as f:
    json.dump({
        'token': ACCESS_TOKEN,
        'expires': TOKEN_EXPIRY,
        'created': time.time(),
        'note': 'Permanent access pass for EVO-AI core data',
    }, f, indent=2)

# Backup originals
BACKUP = '/root/evo-ai/data/vault/originals_backup'
os.makedirs(BACKUP, exist_ok=True)
for filepath in CORE_FILES:
    if os.path.exists(filepath):
        shutil.move(filepath, BACKUP + '/' + os.path.basename(filepath))

print('\nAccess token (valid 1 year):')
print(ACCESS_TOKEN)
print('\nDone.')