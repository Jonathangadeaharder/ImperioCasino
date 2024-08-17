const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const { Pool } = require('pg');

const app = express();
app.use(bodyParser.json());
app.use(cors());

const pool = new Pool({
  user: 'imperiouser',
  host: 'localhost',
  database: 'yourdb',
  password: 'dMMLW6bpgFOq6Z',
  port: 5432,
});

// Route to create a new user
app.post('/createUser', async (req, res) => {
  const { userId } = req.body;
  const startingCoins = 100;

  try {
    const result = await pool.query('SELECT userId FROM users WHERE userId = $1', [userId]);

    if (result.rows.length > 0) {
      return res.status(400).json({ error: 'User already exists' });
    }

    await pool.query(
      'INSERT INTO users (userId, coins) VALUES ($1, $2)',
      [userId, startingCoins]
    );

    res.status(201).json({ message: 'User created successfully', userId, coins: startingCoins });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

app.post('/updateCoins', async (req, res) => {
  const { userId, coins } = req.body;
  try {
    await pool.query(
      `INSERT INTO users (userId, coins) VALUES ($1, $2) 
       ON CONFLICT (userId) 
       DO UPDATE SET coins = EXCLUDED.coins`,
      [userId, coins]
    );
    res.sendStatus(200);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

app.get('/getCoins', async (req, res) => {
  const { userId } = req.query;
  try {
    const result = await pool.query('SELECT coins FROM users WHERE userId = $1', [userId]);
    if (result.rows.length > 0) {
      res.json({ coins: result.rows[0].coins });
    } else {
      res.status(404).json({ error: 'User not found' });
    }
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

app.listen(3001, () => {
  console.log('Server is running on port 3001');
});

