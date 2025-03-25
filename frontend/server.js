const express = require('express');
const session = require('express-session');
const axios = require('axios');
const cookieParser = require('cookie-parser');
const cors = require('cors');

const app = express();
const PORT = 3001;
const BACKEND_URL = 'http://localhost:3000'; // URL вашего бэкенда

app.use(cors({
  origin: 'http://localhost', // Укажите домен вашего фронтенда
  credentials: true
}));
app.use(cookieParser());
app.use(express.json());
app.use(session({
  secret: 'your-secret-key',
  resave: false,
  saveUninitialized: true,
  cookie: { secure: false } // В production используйте secure: true с HTTPS
}));

// Прокси для аутентификации через Telegram
app.post('/auth/telegram', async (req, res) => {
  try {
    const response = await axios.post(`${BACKEND_URL}/auth/telegram`, req.body);
    req.session.token = response.data.token; // Сохраняем токен в сессии
    res.json({ token: response.data.token });
  } catch (error) {
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});

app.get('/', function(req, res) {
  res.sendfile('public/pages/reminders.html');
});
app.get('/', function(req, res) {
  res.sendfile('public/pages/edit_reminders.html');
});
app.get('/', function(req, res) {
  res.sendfile('public/pages/habits.html');
});
app.get('/', function(req, res) {
  res.sendfile('public/pages/trash.html');
});
app.get('/', function(req, res) {
  res.sendfile('public/pages/profile.html');
});
app.get('/', function(req, res) {
  res.sendfile('public/pages/telegram.html');
});

// Прокси для всех остальных запросов к бэкенду
app.use('/api', async (req, res) => {
  if (!req.session.token) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    const config = {
      method: req.method,
      url: `${BACKEND_URL}${req.originalUrl}`,
      headers: {
        'Authorization': `Bearer ${req.session.token}`
      },
      data: req.body
    };

    const response = await axios(config);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});

// Отдача статических файлов
app.use(express.static('public'));

app.listen(PORT, () => {
  console.log(`Node.js proxy server running on http://localhost:${PORT}`);
});