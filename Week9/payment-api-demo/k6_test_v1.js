import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';
const VUS = Number(__ENV.VUS) || 10;
const DURATION = __ENV.DURATION || '30s';

export let options = {
    stages: [
        { duration: '10s', target: VUS },  // Ramp up
        { duration: DURATION, target: VUS }, // Stay at VUS
        { duration: '10s', target: 0 },    // Ramp down
    ],
    thresholds: {
        'http_req_duration': ['p(95)<500'],  // 95% requests < 500ms
        'http_req_failed': ['rate<0.01'],    // Error rate < 1%
        'errors': ['rate<0.01'],
    },
};

/**
 * Test V1 Payment API
 * Tests backward compatibility - V1 shape responses
 */
export default function () {
    // Test 1: Create payment với V1
    const createPayload = JSON.stringify({
        amount: Math.random() * 1000 + 10,
        currency: 'USD',
        source: `card_v1_${__VU}_${Date.now()}`,
    });

    const createRes = http.post(
        `${BASE_URL}/api/v1/payments`,
        createPayload,
        {
            headers: { 'Content-Type': 'application/json' },
            tags: { name: 'v1_create_payment' },
        }
    );

    const createCheck = check(createRes, {
        'v1 create status 201': (r) => r.status === 201,
        'v1 create has id': (r) => {
            if (r.status === 201) {
                const body = r.json();
                return body && body.id !== undefined;
            }
            return false;
        },
        'v1 create returns V1 shape': (r) => {
            if (r.status === 201) {
                const body = r.json();
                // V1 shape: chỉ có fields cơ bản
                return (
                    body.id !== undefined &&
                    body.amount !== undefined &&
                    body.currency !== undefined &&
                    body.source !== undefined &&
                    body.status !== undefined &&
                    body.created_at !== undefined &&
                    body.description === undefined &&  // V1 không có
                    body.metadata === undefined &&      // V1 không có
                    body.updated_at === undefined &&    // V1 không có
                    body.version === undefined          // V1 không có
                );
            }
            return false;
        },
    });

    if (!createCheck) {
        errorRate.add(1);
    }

    let paymentId = null;
    if (createRes.status === 201) {
        const body = createRes.json();
        paymentId = body.id;
    }

    sleep(1);

    // Test 2: Get payment với V1
    if (paymentId) {
        const getRes = http.get(
            `${BASE_URL}/api/v1/payments/${paymentId}`,
            { tags: { name: 'v1_get_payment' } }
        );

        const getCheck = check(getRes, {
            'v1 get status 200': (r) => r.status === 200,
            'v1 get returns V1 shape': (r) => {
                if (r.status === 200) {
                    const body = r.json();
                    // V1 shape: chỉ có fields cơ bản
                    return (
                        body.id !== undefined &&
                        body.amount !== undefined &&
                        body.currency !== undefined &&
                        body.source !== undefined &&
                        body.status !== undefined &&
                        body.created_at !== undefined &&
                        body.description === undefined &&  // V1 không có
                        body.metadata === undefined &&      // V1 không có
                        body.updated_at === undefined &&    // V1 không có
                        body.version === undefined          // V1 không có
                    );
                }
                return false;
            },
            'v1 get correct payment id': (r) => {
                if (r.status === 200) {
                    return r.json().id === paymentId;
                }
                return false;
            },
        });

        if (!getCheck) {
            errorRate.add(1);
        }
    }

    sleep(1);

    // Test 3: Validation tests
    const invalidCreateRes = http.post(
        `${BASE_URL}/api/v1/payments`,
        JSON.stringify({ amount: -10, source: 'card' }),
        {
            headers: { 'Content-Type': 'application/json' },
            tags: { name: 'v1_validation_test' },
        }
    );

    check(invalidCreateRes, {
        'v1 validation rejects invalid amount': (r) => r.status === 400,
    });

    sleep(1);
}

