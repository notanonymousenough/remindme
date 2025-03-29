const express = require('express');
const session = require('express-session');
const axios = require('axios');
const cookieParser = require('cookie-parser');
const cors = require('cors');

const app = express();
const PORT = 80;
const BACKEND_URL = 'http://158.160.114.109:8000'; // URL вашего бэкенда

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
app.get('/api/auth/telegram', async (req, res) => {
  try {
    const response = await axios.post(`${BACKEND_URL}/api/auth/telegram`, req.query);
    console.log(response);
    req.session.token = response.data.token; // Сохраняем токен в сессии
    res.redirect('/reminders');
  } catch (error) {
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});

app.get('/', (req, res) => {
  res.redirect('/reminders');
});
app.get('/reminders', function(req, res) {
  res.sendfile('public/pages/reminders.html');
});
app.get('/edit', function(req, res) {
  res.sendfile('public/pages/edit_reminders.html');
});
app.get('/habits', function(req, res) {
  res.sendfile('public/pages/habits.html');
});
app.get('/trash', function(req, res) {
  res.sendfile('public/pages/trash.html');
});
app.get('/user', function(req, res) {
  res.sendfile('public/pages/user.html');
});
app.get('/telegram', function(req, res) {
  res.sendfile('public/pages/telegram.html');
});
/*app.get('/authed', async(req, res) => {
  try {
    console.log(req.query);
    const response = await axios.post(`${BACKEND_URL}/api/auth/telegram`, req.query);
    console.log(response);
    req.session.token = response.data.token; // Сохраняем токен в сессии
    res.json({ token: response.data.token });
  } catch (error) {
     res.status(error.response?.status || 500).json({ error: error.message });
  }
});*/




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
    console.log(req.session.token)

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