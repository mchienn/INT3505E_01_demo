import requests
import sys
import json
from pprint import pprint
import subprocess
import threading
import time
import os
import re

BASE = 'http://localhost:5000'
TIMEOUT = 5

# For capturing server output when we spawn it
server_process = None
server_logs = []


def start_server_if_needed():
    global server_process, server_logs
    try:
        r = requests.get(BASE + '/api/public', timeout=2)
        return False
    except Exception:
        pass

    project_dir = os.path.dirname(os.path.abspath(__file__))
    python = sys.executable or 'python'
    print(f"Starting api_server.py in {project_dir} using {python} ...")

    server_process = subprocess.Popen(
        [python, 'api_server.py'],
        cwd=project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    def reader():
        for line in server_process.stdout:
            server_logs.append(line)
            print(f"[SERVER] {line}", end='')

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    # wait until server responds or timeout
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            r = requests.get(BASE + '/api/public', timeout=1)
            if r.status_code == 200:
                print('Server started and responding')
                return True
        except Exception:
            time.sleep(0.5)

    print('Timed out waiting for server to start')
    return True


def stop_server_if_started():
    global server_process
    if server_process:
        print('Stopping spawned api_server.py')
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except Exception:
            server_process.kill()
        server_process = None

# Test accounts (as in api_server.py)
ADMIN = ('admin', 'admin123')
USER1 = ('user1', 'user123')

# OAuth client creds (registered in api_server.py)
CLIENT_ID = 'spotify_app_123'
CLIENT_SECRET = 'secret_xyz_spotify'


def ok(msg):
    print(f"[PASS] {msg}")


def warn(msg):
    print(f"[WARN] {msg}")


def fail(msg):
    print(f"[FAIL] {msg}")


def request(method, path, **kwargs):
    url = BASE + path
    try:
        r = requests.request(method, url, timeout=TIMEOUT, **kwargs)
        return r
    except requests.exceptions.ConnectionError:
        print(f"Could not connect to {url}. Is api_server.py running on localhost:5000?")
        sys.exit(1)
    except Exception as e:
        print(f"Request error to {url}: {e}")
        sys.exit(1)


# 1) Protected endpoint without token -> expect 401
# Start server if needed (this will populate server_logs when we spawn the server)
started = start_server_if_needed()

r = request('GET', '/api/protected')
if r.status_code == 401:
    ok("/api/protected rejects unauthenticated requests (401)")
else:
    fail(f"/api/protected returned {r.status_code} for unauthenticated request")


# 2) Login as user1 and test admin endpoint -> expect 403
r_login = request('POST', '/auth/login', json={'username': USER1[0], 'password': USER1[1]})
if r_login.status_code != 200:
    fail(f"Could not login user1: {r_login.status_code} {r_login.text}")
    sys.exit(1)
login_data = r_login.json()
user_token = login_data.get('access_token')
if not user_token:
    fail('No access_token returned for user1')
else:
    ok('Obtained access_token for user1')

r_admin = request('GET', '/api/admin', headers={'Authorization': f'Bearer {user_token}'})
if r_admin.status_code == 403:
    ok("/api/admin correctly returns 403 for non-admin user")
else:
    fail(f"/api/admin returned {r_admin.status_code} (expected 403) with user token")


# 3) /oauth/token with invalid client secret -> expect 401
# Use grant_type=authorization_code with dummy code; client validation happens first
payload = {
    'grant_type': 'authorization_code',
    'code': 'invalid-code',
    'client_id': CLIENT_ID,
    'client_secret': 'wrong-secret',
    'redirect_uri': 'http://localhost:5001/callback'
}
r_token = request('POST', '/oauth/token', json=payload)
if r_token.status_code == 401:
    ok('/oauth/token rejects invalid client credentials (401)')
else:
    warn(f'/oauth/token returned {r_token.status_code} for invalid client credentials; response: {r_token.text}')


# 4) /oauth/revoke without client credentials -> expect 401 (our server requires client auth)
r_revoke_no_auth = request('POST', '/oauth/revoke', json={'token': 'dummy'})
if r_revoke_no_auth.status_code == 401:
    ok('/oauth/revoke requires client authentication (401)')
else:
    warn(f"/oauth/revoke returned {r_revoke_no_auth.status_code} without credentials; response: {r_revoke_no_auth.text}")


# 5) Revoke flow: login -> revoke with valid client creds -> protected endpoint should reject
# Login as user1 already done; user_token variable contains it
print('\n-- Testing revoke flow --')
# verify protected access works first
r_prot_ok = request('GET', '/api/protected', headers={'Authorization': f'Bearer {user_token}'})
if r_prot_ok.status_code == 200:
    ok('Protected endpoint accepted access token before revoke')
else:
    warn(f'Protected endpoint returned {r_prot_ok.status_code} before revoke; response: {r_prot_ok.text}')

# Call revoke with valid client creds
revoke_payload = {'token': user_token, 'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET}
r_revoke = request('POST', '/oauth/revoke', json=revoke_payload)
if r_revoke.status_code == 200:
    ok('/oauth/revoke returned 200 for valid revoke request')
else:
    fail(f'/oauth/revoke returned {r_revoke.status_code} for valid revoke request: {r_revoke.text}')

# Now protected should fail (401)
r_after = request('GET', '/api/protected', headers={'Authorization': f'Bearer {user_token}'})
if r_after.status_code == 401:
    ok('Access token rejected after revoke (blacklisted)')
else:
    fail(f'Access token still valid after revoke: {r_after.status_code}')


# 6) Refresh rotation & reuse detection
print('\n-- Testing refresh token rotation & reuse detection --')
# Login again to obtain a refresh token
r_login2 = request('POST', '/auth/login', json={'username': USER1[0], 'password': USER1[1]})
if r_login2.status_code != 200:
    fail(f"Could not login user1 for refresh test: {r_login2.status_code} {r_login2.text}")
    sys.exit(1)
ld2 = r_login2.json()
orig_refresh = ld2.get('refresh_token')
if not orig_refresh:
    fail('No refresh_token returned for refresh rotation test')
else:
    ok('Obtained refresh_token for rotation test')

# First use of refresh token: expect 200 and a new refresh_token returned
r_refresh1 = request('POST', '/auth/refresh', json={'refresh_token': orig_refresh})
if r_refresh1.status_code == 200:
    ok('First refresh succeeded and should rotate refresh token')
    new_refresh = r_refresh1.json().get('refresh_token')
    if not new_refresh:
        warn('Refresh did not return a new refresh_token (rotation may not be implemented)')
else:
    fail(f'First refresh failed: {r_refresh1.status_code} {r_refresh1.text}')

# Reuse the old refresh token: expect 401 and detection
r_reuse = request('POST', '/auth/refresh', json={'refresh_token': orig_refresh})
if r_reuse.status_code == 401:
    ok('Reuse of old refresh token correctly detected and rejected (401)')
else:
    warn(f'Old refresh token reuse not rejected as expected: {r_reuse.status_code}; response: {r_reuse.text}')


# --- Optional: analyze captured server logs and server config ---
print('\n-- Log analysis & configuration checks --')

# Join logs for analysis
all_logs = "".join(server_logs)

# 1) Look for JWT-like strings (three base64url segments separated by dots)
jwt_pattern = r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"
jwt_matches = re.findall(jwt_pattern, all_logs)
if jwt_matches:
    warn(f"Found {len(jwt_matches)} JWT-like string(s) in server output. This may indicate token leakage.")
    for m in jwt_matches[:5]:
        print(f" - sample: {m[:60]}...")
else:
    ok('No JWT-like strings found in captured server logs')

# 2) Look for long hex strings (possible jti leaks; our jti is 32 hex chars)
hex_pattern = r"\b[a-f0-9]{24,}\b"
hex_matches = re.findall(hex_pattern, all_logs, flags=re.IGNORECASE)
if hex_matches:
    warn(f"Found {len(hex_matches)} long hex string(s) in server output (possible jti or secret leakage)")
    for h in hex_matches[:5]:
        print(f" - sample hex: {h}")
else:
    ok('No long hex strings found in server logs')

# 3) Inspect api_server.py for oauth client redirect URIs that use http:// (warn about insecure redirect URIs)
try:
    project_dir = os.path.dirname(os.path.abspath(__file__))
    server_file = os.path.join(project_dir, 'api_server.py')
    with open(server_file, 'r', encoding='utf-8') as f:
        server_src = f.read()

    # try to locate redirect_uris blocks (allow optional quotes around the key)
    redirect_uris = re.findall(r"['\"]?redirect_uris['\"]?\s*[:=]\s*\[([^\]]+)\]", server_src)
    insecure_found = False
    uris = []
    for block in redirect_uris:
        # find all http/https URIs inside the block
        found = re.findall(r"https?://[^'\"\s,]+", block)
        uris.extend(found)

    for u in uris:
        if u.startswith('http://'):
            warn(f"OAuth client redirect URI uses http:// (not https): {u}")
            insecure_found = True

    if not uris:
        warn('No redirect_uris found in api_server.py (could not parse)')
    elif not insecure_found:
        ok('All discovered OAuth redirect_uris use secure scheme (no http:// found)')
except Exception as e:
    warn(f'Could not inspect api_server.py for redirect_uris: {e}')

# Stop the server if we started it
try:
    if 'started' in globals() and started:
        print('\nStopping spawned server (if any) ...')
        stop_server_if_started()
except Exception:
    pass