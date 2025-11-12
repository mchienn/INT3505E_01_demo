import http from 'k6/http'
import { check, sleep } from 'k6'

// Select scenario via env: TEST_SCENARIO=load|stress|spike|soak|scalability
const SCENARIO = (__ENV.TEST_SCENARIO || 'load').toLowerCase()
const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:5000'

// Default thresholds applied to all scenarios
const DEFAULT_THRESHOLDS = {
	http_req_duration: ['p(95)<2000'],
	http_req_failed: ['rate<0.01'],
}

// Build options dynamically based on chosen scenario so one file can host many tests
export let options = (() => {
	switch (SCENARIO) {
		case 'load':
			// steady load test
			return {
				vus: Number(__ENV.VUS) || 50,
				duration: __ENV.DURATION || '30s',
				thresholds: DEFAULT_THRESHOLDS,
			}
		case 'stress':
			// ramp up to a high number of VUs to find breaking point
			return {
				stages: [
					{ duration: '30s', target: Number(__ENV.START_VUS) || 10 },
					{ duration: '60s', target: Number(__ENV.PEAK_VUS) || 200 },
					{ duration: '30s', target: 0 },
				],
				thresholds: DEFAULT_THRESHOLDS,
			}
		case 'spike':
			// sudden spike: very high traffic for short window
			return {
				scenarios: {
					baseline: {
						executor: 'constant-vus',
						vus: Number(__ENV.BASELINE_VUS) || 5,
						duration: '20s',
					},
					spike: {
						executor: 'constant-vus',
						vus: Number(__ENV.SPIKE_VUS) || 300,
						duration: __ENV.SPIKE_DURATION || '15s',
						startTime: '20s',
					},
				},
				thresholds: DEFAULT_THRESHOLDS,
			}
		case 'soak':
		case 'endurance':
			// long-running soak test (use small VUs for long duration locally)
			return {
				vus: Number(__ENV.VUS) || 10,
				duration: __ENV.DURATION || '30m',
				thresholds: DEFAULT_THRESHOLDS,
			}
		case 'scalability':
			// scalability: multiple stages that increase load gradually
			return {
				stages: [
					{ duration: '30s', target: Number(__ENV.S1) || 10 },
					{ duration: '60s', target: Number(__ENV.S2) || 50 },
					{ duration: '60s', target: Number(__ENV.S3) || 150 },
					{ duration: '30s', target: 0 },
				],
				thresholds: DEFAULT_THRESHOLDS,
			}
		default:
			return {
				vus: 5,
				duration: '20s',
				thresholds: DEFAULT_THRESHOLDS,
			}
	}
})()

// Shared scenario workload: login + list + create + update + delete
function runWorkflow() {
	// 1) Login
	const loginRes = http.post(
		`${BASE_URL}/api/sessions`,
		JSON.stringify({ username: 'admin', password: 'secret' }),
		{ headers: { 'Content-Type': 'application/json' }, tags: { name: 'login' } }
	)

	check(loginRes, {
		'login status 200': (r) => r.status === 200,
		'login returned token': (r) =>
			r.status === 200 && r.json && r.json('token') !== undefined,
	})

	let token = ''
	if (loginRes.status === 200) {
		token = loginRes.json('token')
	}

	// 2) GET products
	const getRes = http.get(`${BASE_URL}/api/products`, {
		tags: { name: 'get_products' },
	})
	check(getRes, { 'get products 200': (r) => r.status === 200 })

	// 3) POST create product (auth)
	const prodName = `k6-${__VU}-${Date.now()}`
	const createRes = http.post(
		`${BASE_URL}/api/products`,
		JSON.stringify({
			name: prodName,
			price: Math.round(Math.random() * 10000) / 100,
		}),
		{
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`,
			},
			tags: { name: 'create_product' },
		}
	)

	check(createRes, { 'create 201': (r) => r.status === 201 })
	let createdId = null
	if (createRes.status === 201)
		createdId = createRes.json('id') || createRes.json().id

	// 4) PUT update
	if (createdId) {
		const updRes = http.put(
			`${BASE_URL}/api/products/${createdId}`,
			JSON.stringify({
				name: `${prodName} (u)`,
				price: Math.round(Math.random() * 10000) / 100,
			}),
			{
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${token}`,
				},
				tags: { name: 'update_product' },
			}
		)
		check(updRes, { 'update 200': (r) => r.status === 200 })
	}

	// 5) DELETE
	if (createdId) {
		const delRes = http.del(`${BASE_URL}/api/products/${createdId}`, null, {
			headers: { Authorization: `Bearer ${token}` },
			tags: { name: 'delete_product' },
		})
		check(delRes, { 'delete 204': (r) => r.status === 204 })
	}

	// short sleep to avoid tight loop unless the scenario is very small
	sleep(Number(__ENV.SLEEP) || 1)
}

export default function () {
	// In case scenarios like 'spike' define multiple executors, default function will be executed per VU as defined by k6
	runWorkflow()
}
