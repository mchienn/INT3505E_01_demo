require('dotenv').config();
const express = require('express');
const app = express();

app.use(express.json());

const PORT = process.env.PORT || 3000;
const MESSAGE = process.env.MESSAGE || 'Hello from Default Environment!';

// In-memory data store
let items = [
  { id: 1, name: 'Item 1', description: 'This is item 1' },
  { id: 2, name: 'Item 2', description: 'This is item 2' }
];

// Home endpoint
app.get('/', (req, res) => {
  res.json({
    message: MESSAGE,
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development',
    endpoints: [
      'GET /health',
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
  res.json(items);
});

// GET single item
app.get('/items/:id', (req, res) => {
  const item = items.find(i => i.id === parseInt(req.params.id));
  if (!item) return res.status(404).json({ message: 'Item not found' });
  res.json(item);
});

// POST create item
app.post('/items', (req, res) => {
  if (!req.body.name) {
    return res.status(400).json({ message: 'Name is required' });
  }
  const newItem = {
    id: items.length + 1,
    name: req.body.name,
    description: req.body.description || ''
  };
  items.push(newItem);
  res.status(201).json(newItem);
});

// PUT update item
app.put('/items/:id', (req, res) => {
  const item = items.find(i => i.id === parseInt(req.params.id));
  if (!item) return res.status(404).json({ message: 'Item not found' });

  item.name = req.body.name || item.name;
  item.description = req.body.description || item.description;

  res.json(item);
});

// DELETE item
app.delete('/items/:id', (req, res) => {
  const itemIndex = items.findIndex(i => i.id === parseInt(req.params.id));
  if (itemIndex === -1) return res.status(404).json({ message: 'Item not found' });

  const deletedItem = items.splice(itemIndex, 1);
  res.json(deletedItem[0]);
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
