require('dotenv').config();
const express = require('express');
const winston = require('winston');
const client = require('prom-client');
const app = express();

app.use(express.json());

const PORT = process.env.PORT || 3000;
const MESSAGE = process.env.MESSAGE || 'Hello from Default Environment!';

// Configure Winston Logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

// Prometheus Metrics
const register = new client.Registry();

// Add default metrics (cpu, memory, etc.)
client.collectDefaultMetrics({ register });

const httpRequestDurationMicroseconds = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.1, 0.5, 1, 1.5, 2, 5]
});

const httpRequestsTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code']
});

register.registerMetric(httpRequestDurationMicroseconds);
register.registerMetric(httpRequestsTotal);

// Request Logging & Monitoring Middleware
app.use((req, res, next) => {
  const start = Date.now();

  res.on('finish', () => {
    const duration = Date.now() - start;
    const durationSeconds = duration / 1000;

    // Log with Winston
    logger.info({
      message: 'Request processed',
      method: req.method,
      url: req.originalUrl,
      status: res.statusCode,
      duration: `${duration}ms`
    });

    // Update Prometheus Metrics
    // Use req.route ? req.route.path : req.path to avoid high cardinality with IDs
    const route = req.route ? req.route.path : req.path;

    httpRequestDurationMicroseconds
      .labels(req.method, route, res.statusCode)
      .observe(durationSeconds);

    httpRequestsTotal
      .labels(req.method, route, res.statusCode)
      .inc();
  });
  next();
});

// In-memory data store
let items = [
  { id: 1, name: 'Item 1', description: 'This is item 1' },
  { id: 2, name: 'Item 2', description: 'This is item 2' }
];

// Metrics Endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

// Home endpoint
app.get('/', (req, res) => {
  logger.info('Home endpoint accessed');
  res.json({
    message: MESSAGE,
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development',
    endpoints: [
      'GET /health',
      'GET /metrics',
      'GET /items',
      'GET /items/:id',
      'POST /items',
      'PUT /items/:id',
      'DELETE /items/:id'
    ]
  });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'UP',
    uptime: process.uptime(),
    timestamp: new Date().toISOString()
  });
});

// CRUD Operations for Items

// GET all items
app.get('/items', (req, res) => {
  logger.info('Fetching all items');
  res.json(items);
});

// GET single item
app.get('/items/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const item = items.find(i => i.id === id);

  if (!item) {
    logger.warn(`Item not found: ${id}`);
    return res.status(404).json({ message: 'Item not found' });
  }

  res.json(item);
});

// POST create item
app.post('/items', (req, res) => {
  if (!req.body.name) {
    logger.error('Validation error: Name is required');
    return res.status(400).json({ message: 'Name is required' });
  }
  const newItem = {
    id: items.length + 1,
    name: req.body.name,
    description: req.body.description || ''
  };
  items.push(newItem);
  logger.info(`Item created: ${newItem.id}`);
  res.status(201).json(newItem);
});

// PUT update item
app.put('/items/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const item = items.find(i => i.id === id);

  if (!item) {
    logger.warn(`Update failed: Item not found ${id}`);
    return res.status(404).json({ message: 'Item not found' });
  }

  item.name = req.body.name || item.name;
  item.description = req.body.description || item.description;

  logger.info(`Item updated: ${id}`);
  res.json(item);
});

// DELETE item
app.delete('/items/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const itemIndex = items.findIndex(i => i.id === id);

  if (itemIndex === -1) {
    logger.warn(`Delete failed: Item not found ${id}`);
    return res.status(404).json({ message: 'Item not found' });
  }

  const deletedItem = items.splice(itemIndex, 1);
  logger.info(`Item deleted: ${id}`);
  res.json(deletedItem[0]);
});

app.listen(PORT, () => {
  logger.info(`Server is running on port ${PORT}`);
});
