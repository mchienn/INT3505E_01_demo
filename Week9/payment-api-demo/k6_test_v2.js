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
 * Test V2 Payment API
 * Tests enriched V2 shape responses với description và metadata
 */
export default function () {
    // Test 1: Create payment với V2 (full fields)
    const createPayload = JSON.stringify({
        amount: Math.random() * 1000 + 10,
        currency: 'USD',
        source: `card_v2_${__VU}_${Date.now()}`,
        description: `Payment for order #${Math.floor(Math.random() * 1000)}`,
        metadata: {
            order_id: `${Math.floor(Math.random() * 1000)}`,
            customer_id: `${Math.floor(Math.random() * 10000)}`,
            test_run: 'k6_v2',
        },
    });

    const createRes = http.post(
        `${BASE_URL}/api/v2/payments`,
        createPayload,
        {
            headers: { 'Content-Type': 'application/json' },
            tags: { name: 'v2_create_payment' },
        }
    );

    const createCheck = check(createRes, {
        'v2 create status 201': (r) => r.status === 201,
        'v2 create has id': (r) => {
            if (r.status === 201) {
                const body = r.json();
                return body && body.id !== undefined;
            }
            return false;
        },
        'v2 create returns V2 shape': (r) => {
            if (r.status === 201) {
                const body = r.json();
                // V2 shape: có đầy đủ fields
                return (
                    body.id !== undefined &&
                    body.amount !== undefined &&
                    body.currency !== undefined &&
                    body.source !== undefined &&
                    body.status !== undefined &&
                    body.created_at !== undefined &&
                    body.description !== undefined &&  // V2 có
                    body.metadata !== undefined &&      // V2 có
                    body.updated_at !== undefined &&    // V2 có
                    body.version === 'v2'               // V2 có version
                );
            }
            return false;
        },
        'v2 create has description': (r) => {
            if (r.status === 201) {
                return r.json().description !== null && r.json().description !== undefined;
            }
            return false;
        },
        'v2 create has metadata': (r) => {
            if (r.status === 201) {
                const metadata = r.json().metadata;
                return metadata !== null && metadata !== undefined && typeof metadata === 'object';
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

    // Test 2: Get payment với V2
    if (paymentId) {
        const getRes = http.get(
            `${BASE_URL}/api/v2/payments/${paymentId}`,
            { tags: { name: 'v2_get_payment' } }
        );

        const getCheck = check(getRes, {
            'v2 get status 200': (r) => r.status === 200,
            'v2 get returns V2 shape': (r) => {
                if (r.status === 200) {
                    const body = r.json();
                    // V2 shape: có đầy đủ fields
                    return (
                        body.id !== undefined &&
                        body.amount !== undefined &&
                        body.description !== undefined &&  // V2 có
                        body.metadata !== undefined &&      // V2 có
                        body.updated_at !== undefined &&    // V2 có
                        body.version !== undefined          // V2 có
                    );
                }
                return false;
            },
            'v2 get correct payment id': (r) => {
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

    // Test 3: Update payment (V2 only)
    if (paymentId) {
        const updatePayload = JSON.stringify({
            status: 'completed',
            metadata: {
                processed_by: 'k6_test',
                processed_at: new Date().toISOString(),
            },
        });

        const updateRes = http.patch(
            `${BASE_URL}/api/v2/payments/${paymentId}`,
            updatePayload,
            {
                headers: { 'Content-Type': 'application/json' },
                tags: { name: 'v2_update_payment' },
            }
        );

        const updateCheck = check(updateRes, {
            'v2 update status 200': (r) => r.status === 200,
            'v2 update changes status': (r) => {
                if (r.status === 200) {
                    return r.json().status === 'completed';
                }
                return false;
            },
            'v2 update merges metadata': (r) => {
                if (r.status === 200) {
                    const metadata = r.json().metadata;
                    return metadata && metadata.processed_by === 'k6_test';
                }
                return false;
            },
        });

        if (!updateCheck) {
            errorRate.add(1);
        }
    }

    sleep(1);

    // Test 4: List payments với filtering
    const listRes = http.get(
        `${BASE_URL}/api/v2/payments?status=pending&limit=10&offset=0`,
        { tags: { name: 'v2_list_payments' } }
    );

    const listCheck = check(listRes, {
        'v2 list status 200': (r) => r.status === 200,
        'v2 list returns correct structure': (r) => {
            if (r.status === 200) {
                const body = r.json();
                return (
                    body.payments !== undefined &&
                    Array.isArray(body.payments) &&
                    body.total !== undefined &&
                    body.limit !== undefined &&
                    body.offset !== undefined
                );
            }
            return false;
        },
        'v2 list payments have V2 shape': (r) => {
            if (r.status === 200) {
                const body = r.json();
                if (body.payments && body.payments.length > 0) {
                    const firstPayment = body.payments[0];
                    return (
                        firstPayment.id !== undefined &&
                        firstPayment.version !== undefined
                    );
                }
                return true; // Empty list is OK
            }
            return false;
        },
    });

    if (!listCheck) {
        errorRate.add(1);
    }

    sleep(1);

    // Test 5: Create payment V2 minimal (chỉ required fields)
    const minimalPayload = JSON.stringify({
        amount: Math.random() * 1000 + 10,
        source: `card_v2_minimal_${__VU}_${Date.now()}`,
    });

    const minimalRes = http.post(
        `${BASE_URL}/api/v2/payments`,
        minimalPayload,
        {
            headers: { 'Content-Type': 'application/json' },
            tags: { name: 'v2_create_minimal' },
        }
    );

    check(minimalRes, {
        'v2 create minimal status 201': (r) => r.status === 201,
        'v2 create minimal has V2 shape': (r) => {
            if (r.status === 201) {
                const body = r.json();
                return (
                    body.version === 'v2' &&
                    body.description !== undefined &&  // Field có nhưng có thể null
                    body.metadata !== undefined        // Field có
                );
            }
            return false;
        },
    });

    sleep(1);

    // Test 6: Validation tests
    const invalidCreateRes = http.post(
        `${BASE_URL}/api/v2/payments`,
        JSON.stringify({ amount: -10, source: 'card' }),
        {
            headers: { 'Content-Type': 'application/json' },
            tags: { name: 'v2_validation_test' },
        }
    );

    check(invalidCreateRes, {
        'v2 validation rejects invalid amount': (r) => r.status === 400,
    });

    sleep(1);
}

