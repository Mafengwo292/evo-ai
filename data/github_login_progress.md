# GitHub Login Status (2026-09-18)

## Issue Identified
- Username/email: 23087329@qq.com
- Password: Hu8384jian051 (works - we get past initial auth)
- 2FA: ENABLED (email-based device verification)
- First OTP provided: 874987 → expired before submission completed

## Why It Failed
1. TOTP/email codes valid for 30-60s
2. My session was set up at one time, code submitted ~30s later
3. Also, the form required multi-step (login → 2FA page → submit OTP)

## What's Needed
A FRESH 6-digit 2FA code, submitted IMMEDIATELY (within 30s of generation)

## My Status
- Cookies saved to: /workspace/evo-ai/data/github_cookies.txt
- 2FA form URL: https://github.com/sessions/verified-device
- 2FA field: name="otp"

## Working flow when user provides new code:
1. User opens a new email from GitHub
2. Reads new 6-digit code
3. Sends it to me within 30 seconds
4. I submit to /sessions/verified-device immediately
5. Get logged_in=yes session cookie
6. Use that cookie for API calls

## What to do meanwhile
- Prepare the GitHub repo structure
- Write all README/docs
- Pre-stage EvoAgentX PR
