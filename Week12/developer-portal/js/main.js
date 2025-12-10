document.addEventListener('DOMContentLoaded', () => {
    const methodSelect = document.getElementById('method');
    const bodyGroup = document.getElementById('bodyGroup');
    const sendBtn = document.getElementById('sendBtn');
    const responseArea = document.getElementById('responseArea');
    const responseBody = document.getElementById('responseBody');
    const statusCode = document.getElementById('statusCode');
    const latency = document.getElementById('latency');

    // Toggle Body visibility
    function toggleBody() {
        const method = methodSelect.value;
        if (method === 'POST' || method === 'PUT' || method === 'PATCH') {
            bodyGroup.style.display = 'block';
        } else {
            bodyGroup.style.display = 'none';
        }
    }

    methodSelect.addEventListener('change', toggleBody);
    toggleBody(); // Init

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

    // Handle Send
    sendBtn.addEventListener('click', () => {
        // UI State: Loading
        sendBtn.textContent = 'Sending...';
        sendBtn.disabled = true;
        responseArea.style.opacity = '0.5';

        // Simulate Network Request
        setTimeout(() => {
            const method = methodSelect.value;
            const data = mockResponses[method] || { "message": "Resource deleted successfully" };

            // Randomize Latency
            const lat = Math.floor(Math.random() * 200) + 50;

            // Update UI
            responseBody.textContent = JSON.stringify(data, null, 2);
            statusCode.textContent = '200 OK';
            latency.textContent = `${lat}ms`;

            // Reset State
            responseArea.style.opacity = '1';
            responseArea.style.pointerEvents = 'all';
            sendBtn.textContent = 'Send Request';
            sendBtn.disabled = false;
        }, 800);
    });
});
