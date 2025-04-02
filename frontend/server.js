const express = require('express');
const session = require('express-session');
const axios = require('axios');
const cookieParser = require('cookie-parser');
const cors = require('cors');


const app = express();
require('dotenv').config();
const PORT = process.env.PORT || 80;
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
    const response = await axios.post(`http://localhost:8000/v1/auth/telegram`, req.body);
    req.session.token = response.data; // Сохраняем токен в сессии
    console.log(response);
    res.redirect('/reminders');
  } catch (error) {
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});
const checkToken = (req, res, next) => {
  if (req.path.startsWith('/css/') || req.path.startsWith('/js/') || req.path.startsWith('/assets/')) {
    return next();
  }
  if (!req.session.token) { // Проверяем, сохранён ли токен в сессии
    if (req.path !== '/telegram') { // Если мы не на странице /telegram
      return res.redirect('/telegram'); // Перенаправляем на /telegram
    }
  }
  next(); // Если токен есть или мы на /telegram, продолжаем обработку
};

app.use(checkToken);


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

app.use('/api/*', async (req, res) => {
  if (!req.session.token) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    const options = {
      method: req.method,
      url: 'http://localhost:8000/v1/reminders',
      data: req.method === 'POST' || req.method === 'PUT' ? req.body : undefined, // Передаем body только для POST и PUT
      headers: {
        'Content-Type': 'application/json', // Установите нужные заголовки
      },
    };

    const response = await axios(options);
    res.status(response.status).json(response.data);
    
  } catch (error) {
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});

// Отдача статических файлов
app.use(express.static('public'));

app.listen(PORT, () => {
  console.log(`Node.js proxy server running on http://localhost:${PORT}`);
});