document.addEventListener('DOMContentLoaded', () => {
    // Mode toggles
    const btnDemo = document.getElementById('btnDemo');
    const btnLive = document.getElementById('btnLive');
    const authGroup = document.getElementById('authGroup');
    const apiKeyInput = document.getElementById('apiKeyInput');

    // Inputs
    const methodSelect = document.getElementById('method');
    const urlInput = document.getElementById('url');
    const bodyGroup = document.getElementById('bodyGroup');
    const requestBody = document.getElementById('requestBody');
    const codeSnippet = document.getElementById('codeSnippet');

    // Actions & Outputs
    const sendBtn = document.getElementById('sendBtn');
    const responseArea = document.getElementById('responseArea');
    const responseBody = document.getElementById('responseBody');
    const statusCode = document.getElementById('statusCode');
    const latency = document.getElementById('latency');

    let currentMode = 'demo'; // demo | live

    // Toggle Mode Logic
    function setMode(mode) {
        currentMode = mode;
        if (mode === 'live') {
            btnLive.style.background = 'var(--accent-primary)';
            btnLive.style.color = 'white';
            btnDemo.style.background = 'transparent';
            btnDemo.style.color = 'var(--text-secondary)';
            authGroup.style.display = 'block';
        } else {
            btnDemo.style.background = 'var(--accent-primary)';
            btnDemo.style.color = 'white';
            btnLive.style.background = 'transparent';
            btnLive.style.color = 'var(--text-secondary)';
            authGroup.style.display = 'none';
        }
        updateCodeSnippet();
    }

    btnDemo.addEventListener('click', () => setMode('demo'));
    btnLive.addEventListener('click', () => setMode('live'));

    // Toggle Body Logic
    function toggleBody() {
        const method = methodSelect.value;
        if (method === 'POST' || method === 'PUT' || method === 'PATCH') {
            bodyGroup.style.display = 'block';
        } else {
            bodyGroup.style.display = 'none';
        }
        updateCodeSnippet();
    }

    // Generate Code Snippet (cURL)
    function updateCodeSnippet() {
        const method = methodSelect.value;
        const url = urlInput.value;
        const body = requestBody.value;

        let snippet = `curl -X ${method} "${url}"`;

        // Add Headers
        snippet += ` \\\n  -H "Content-Type: application/json"`;

        if (currentMode === 'live') {
            const token = apiKeyInput.value || 'YOUR_API_KEY';
            snippet += ` \\\n  -H "Authorization: ${token}"`;
        }

        // Add Body
        if ((method === 'POST' || method === 'PUT') && body) {
            // Minify JSON for curl
            try {
                const minified = JSON.stringify(JSON.parse(body));
                snippet += ` \\\n  -d '${minified}'`;
            } catch (e) {
                snippet += ` \\\n  -d '${body.replace(/\n/g, '')}'`;
            }
        }

        codeSnippet.textContent = snippet;
    }

    // Event Listeners for Dynamic Updates
    methodSelect.addEventListener('change', toggleBody);
    urlInput.addEventListener('input', updateCodeSnippet);
    requestBody.addEventListener('input', updateCodeSnippet);
    apiKeyInput.addEventListener('input', updateCodeSnippet);

    // Initial call
    toggleBody();

    // Mock API Responses
    const mockResponses = {
        'GET': {
            'data': [
                {
                    "id": "post_1",
                    "title": "Welcome to the API",
                    "content": "This is a sample post retrieved from the sandbox.",
                    "created_at": "2023-11-20T10:00:00Z"
                },
                {
                    "id": "post_2",
                    "title": "Developer Experience",
                    "content": "Building great tools for developers.",
                    "created_at": "2023-11-21T15:30:00Z"
                }
            ],
            'meta': {
                'page': 1,
                'total': 2
            }
        },
        'POST': {
            "id": "post_3",
            "title": "My Post",
            "content": "Hello World",
            "status": "published",
            "created_at": new Date().toISOString()
        }
    };

    // Handle Send Button
    sendBtn.addEventListener('click', () => {
        // UI State: Loading
        sendBtn.textContent = 'Sending...';
        sendBtn.disabled = true;
        responseArea.style.opacity = '0.5';

        // Simulate Network Request
        setTimeout(() => {
            const method = methodSelect.value;
            let data = mockResponses[method] || { "message": "Resource deleted successfully" };
            let status = '200 OK';

            // Simulate Error if in Live Mode without Key
            if (currentMode === 'live') {
                const key = apiKeyInput.value;
                if (!key || key.includes('sk_live_...')) {
                    status = '401 Unauthorized';
                    data = {
                        "error": {
                            "code": 401,
                            "message": "Invalid authentication credentials"
                        }
                    };
                }
            }

            // Randomize Latency
            const lat = Math.floor(Math.random() * 200) + 50;

            // Update UI
            responseBody.textContent = JSON.stringify(data, null, 2);
            statusCode.innerHTML = status;

            // Colorize Status
            if (status.startsWith('2')) {
                statusCode.className = 'status-badge status-200';
            } else {
                statusCode.className = 'status-badge status-400';
            }

            latency.textContent = `${lat}ms`;

            // Reset State
            responseArea.style.opacity = '1';
            responseArea.style.pointerEvents = 'all';
            sendBtn.textContent = 'Send Request';
            sendBtn.disabled = false;
        }, 800);
    });
});
