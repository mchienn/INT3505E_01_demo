from flask import Flask, request, redirect, session, jsonify
import requests
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# OAuth 2.0 Configuration
OAUTH_CONFIG = {
    'client_id': 'third_party_app',
    'client_secret': 'secret_xyz_third_party',
    'authorization_endpoint': 'http://localhost:5000/oauth/authorize',
    'token_endpoint': 'http://localhost:5000/oauth/token',
    'userinfo_endpoint': 'http://localhost:5000/oauth/userinfo',
    'redirect_uri': 'http://localhost:5001/callback',
    'scope': 'profile email'
}


@app.route('/')
def home():
    """Home page"""
    
    # Check if user is logged in
    if 'user' in session:
        user = session['user']
        
        # Logged in - show user info
        page = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Third-Party App</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                }}
                .success {{
                    background: #4CAF50;
                    color: white;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .card {{
                    border: 1px solid #ddd;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
                button {{
                    background: #2196F3;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    margin: 5px;
                }}
                button:hover {{
                    background: #0b7dda;
                }}
                .logout {{
                    background: #f44336;
                }}
                .logout:hover {{
                    background: #da190b;
                }}
            </style>
        </head>
        <body>
            <h1>Third-Party Application</h1>
            
            <div class="success">
                ✅ Logged in successfully via OAuth 2.0!
            </div>
            
            <div class="card">
                <h3>User Information</h3>
                <p><strong>User ID:</strong> {user.get('sub', 'N/A')}</p>
                <p><strong>Username:</strong> {user.get('username', 'N/A')}</p>
                <p><strong>Email:</strong> {user.get('email', 'N/A')}</p>
                <p><strong>Name:</strong> {user.get('name', 'N/A')}</p>
                <p><strong>Role:</strong> {user.get('role', 'N/A')}</p>
            </div>
            
            <div style="margin-top: 20px;">
                <button onclick="location.href='/test-api'">Test API Call</button>
                <button class="logout" onclick="location.href='/logout'">Logout</button>
            </div>
        </body>
        </html>
        '''
        return page
    
    # Not logged in - show login page
    login_page = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Third-Party App - Login</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 500px;
                margin: 100px auto;
                padding: 20px;
                text-align: center;
            }}
            .card {{
                border: 1px solid #ddd;
                padding: 40px;
                border-radius: 8px;
            }}
            h1 {{
                margin-bottom: 30px;
            }}
            .btn-login {{
                display: inline-block;
                background: #4285f4;
                color: white;
                text-decoration: none;
                padding: 15px 40px;
                border-radius: 5px;
                font-size: 16px;
            }}
            .btn-login:hover {{
                background: #357ae8;
            }}
            .info {{
                margin-top: 30px;
                padding: 20px;
                background: #f5f5f5;
                border-radius: 5px;
                text-align: left;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Third-Party Application</h1>
            <p>Demo OAuth 2.0 Login</p>
            
            <a href="/login" class="btn-login">
                🔐 Login with OAuth Server
            </a>
            
            <div class="info">
                <strong>OAuth 2.0 Flow:</strong><br><br>
                1. Click "Login with OAuth Server"<br>
                2. Redirect to OAuth server (port 5000)<br>
                3. Login with your account<br>
                4. Authorize this app<br>
                5. Get redirected back with user info<br><br>
                <strong>Test accounts:</strong><br>
                • admin / admin123<br>
                • user1 / user123
            </div>
        </div>
    </body>
    </html>
    '''
    return login_page


@app.route('/login')
def login():
    """Redirect to OAuth authorization"""
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    # Build authorization URL
    auth_url = (
        f"{OAUTH_CONFIG['authorization_endpoint']}"
        f"?client_id={OAUTH_CONFIG['client_id']}"
        f"&redirect_uri={OAUTH_CONFIG['redirect_uri']}"
        f"&response_type=code"
        f"&scope={OAUTH_CONFIG['scope']}"
        f"&state={state}"
    )
    
    print(f"\n[App] 🔄 Redirecting to OAuth server...")
    print(f"[App] 📍 URL: {auth_url}\n")
    
    return redirect(auth_url)


@app.route('/callback')
def callback():    
    # Verify state (CSRF protection)
    state = request.args.get('state')
    if state != session.get('oauth_state'):
        return "❌ Invalid state parameter (CSRF protection)", 400
    
    # Get authorization code
    code = request.args.get('code')
    if not code:
        error = request.args.get('error', 'unknown_error')
        return f"❌ Authorization failed: {error}", 400
    
    print(f"\n[App] ✅ Received authorization code: {code[:20]}...")
    print(f"[App] 🔄 Exchanging code for access token...")
    
    # Exchange code for access token
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': OAUTH_CONFIG['client_id'],
        'client_secret': OAUTH_CONFIG['client_secret'],
        'redirect_uri': OAUTH_CONFIG['redirect_uri']
    }
    
    try:
        # Call token endpoint
        token_response = requests.post(
            OAUTH_CONFIG['token_endpoint'],
            json=token_data
        )
        
        if token_response.status_code != 200:
            print(f"[App] ❌ Token exchange failed: {token_response.text}")
            return f"Token exchange failed: {token_response.text}", 400
        
        token_result = token_response.json()
        access_token = token_result['access_token']
        
        print(f"[App] ✅ Access token received: {access_token[:20]}...")
        print(f"[App] 🔄 Fetching user info...")
        
        # Get user info
        userinfo_response = requests.get(
            OAUTH_CONFIG['userinfo_endpoint'],
            headers={'Authorization': f"Bearer {access_token}"}
        )
        
        if userinfo_response.status_code != 200:
            return f"Failed to get user info: {userinfo_response.text}", 400
        
        user_info = userinfo_response.json()
        
        print(f"[App] ✅ User logged in: {user_info.get('name')} ({user_info.get('email')})")
        print(f"[App] 🎉 OAuth 2.0 flow complete!\n")
        
        # Store in session
        session['user'] = user_info
        session['access_token'] = access_token
        
        return redirect('/')
        
    except Exception as e:
        print(f"[App] ❌ Error: {str(e)}\n")
        return f"Error: {str(e)}", 500


@app.route('/test-api')
def test_api():
    """Test calling OAuth API"""
    
    if 'access_token' not in session:
        return redirect('/')
    
    access_token = session['access_token']
    
    # Call userinfo endpoint
    response = requests.get(
        OAUTH_CONFIG['userinfo_endpoint'],
        headers={'Authorization': f"Bearer {access_token}"}
    )
    
    page = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Test</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 700px;
                margin: 50px auto;
                padding: 20px;
            }}
            .card {{
                border: 1px solid #ddd;
                padding: 20px;
                border-radius: 5px;
            }}
            pre {{
                background: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            button {{
                background: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 20px;
            }}
            .success {{
                background: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 15px;
            }}
        </style>
    </head>
    <body>
        <h1>OAuth 2.0 API Test</h1>
        <div class="card">
            <div class="success">
                ✅ Successfully called OAuth server API with access token
            </div>
            
            <p><strong>Endpoint:</strong> {OAUTH_CONFIG['userinfo_endpoint']}</p>
            <p><strong>Method:</strong> GET</p>
            <p><strong>Authorization:</strong> Bearer {access_token[:30]}...</p>
            <p><strong>Status:</strong> {response.status_code}</p>
            
            <h3>Response:</h3>
            <pre>{response.text}</pre>
            
            <button onclick="location.href='/'">← Back</button>
        </div>
    </body>
    </html>
    '''
    return page





@app.route('/logout')
def logout():
    """Logout"""
    access_token = session.get('access_token')

    if access_token:
        revoke_payload = {
            'token': access_token,
            'client_id': OAUTH_CONFIG['client_id'],
            'client_secret': OAUTH_CONFIG['client_secret']
        }
        try:
            resp = requests.post(
                'http://localhost:5000/oauth/revoke',
                json=revoke_payload,
                timeout=5
            )
            if resp.status_code == 200:
                print("[App] 🔒 Access token revoked at provider")
            else:
                print(f"[App] ⚠️ Revoke call returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[App] ❌ Error calling revoke endpoint: {e}")

    session.clear()
    return redirect('/')


if __name__ == '__main__':
    print("Third-Party Application - OAuth 2.0 Client Demo")
    print(f"\n🔑 Then open: http://localhost:5001")
    
    app.run(debug=True, port=5001)
