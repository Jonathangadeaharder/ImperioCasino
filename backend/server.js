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
    const result = await pool.query('SELECT coins FROM users WHERE userid = $1', [userId]);
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

