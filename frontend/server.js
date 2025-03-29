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

app.get('/api/reminders/', function(req, res) {
  const reminders = [
    {
      "id": "r1a2b3c4d5",
      "userId": "usr_12345",
      "text": "Купить молоко",
      "time": "2023-12-02T18:30:00Z",
      "tags": ["покупки"],
      "status": "active",
      "removed": false,
      "createdAt": "2023-11-30T22:15:00Z",
      "updatedAt": "2023-11-30T22:15:00Z",
      "completedAt": null,
      "notificationSent": false
    },
    {
      "id": "r2e3f4g5h6",
      "userId": "usr_12345",
      "text": "Позвонить маме",
      "time": "2023-12-02T18:30:00Z",
      "tags": ["семья"],
      "status": "active",
      "removed": false,
      "createdAt": "2023-11-28T14:20:00Z",
      "updatedAt": "2023-11-29T10:05:00Z",
      "completedAt": null,
      "notificationSent": false
    },
    {
      "id": "r3i4j5k6l7",
      "userId": "usr_54321",
      "text": "Оплатить счет за интернет",
      "time": "2023-11-25T12:00:00Z",
      "tags": ["платежи"],
      "status": "completed",
      "removed": false,
      "createdAt": "2023-11-20T08:45:00Z",
      "updatedAt": "2023-11-25T13:10:00Z",
      "completedAt": "2023-11-25T13:10:00Z",
      "notificationSent": true
    },
    {
      "id": "r4m5n6o7p8",
      "userId": "usr_12345",
      "text": "Подготовить презентацию для встречи",
      "time": "2023-11-28T09:30:00Z",
      "tags": ["работа"],
      "status": "forgotten",
      "removed": false,
      "createdAt": "2023-11-26T16:00:00Z",
      "updatedAt": "2023-11-29T10:00:00Z",
      "completedAt": null,
      "notificationSent": true
    },
    {
      "id": "r5q6r7s8t9",
      "userId": "usr_67890",
      "text": "Записаться к стоматологу",
      "time": "2023-12-10T14:15:00Z",
      "tags": ["здоровье"],
      "status": "active",
      "removed": false,
      "createdAt": "2023-11-27T19:30:00Z",
      "updatedAt": "2023-11-27T19:30:00Z",
      "completedAt": null,
      "notificationSent": false
    },
    {
      "id": "r6u7v8w9x0",
      "userId": "usr_54321",
      "text": "Забрать посылку с почты",
      "time": "2023-12-01T16:00:00Z",
      "tags": ["дела"],
      "status": "active",
      "removed": false,
      "createdAt": "2023-11-29T11:45:00Z",
      "updatedAt": "2023-11-29T11:45:00Z",
      "completedAt": null,
      "notificationSent": false
    },
    {
      "id": "r7y8z9a0b1",
      "userId": "usr_67890",
      "text": "Дедлайн по проекту",
      "time": "2023-11-30T18:00:00Z",
      "tags": ["работа"],
      "status": "completed",
      "removed": false,
      "createdAt": "2023-11-15T09:20:00Z",
      "updatedAt": "2023-11-30T17:50:00Z",
      "completedAt": "2023-11-30T17:50:00Z",
      "notificationSent": true
    },
    {
      "id": "r8c9d0e1f2",
      "userId": "usr_12345",
      "text": "Совещание с командой",
      "time": "2023-11-24T10:00:00Z",
      "tags": ["встреча"],
      "status": "active",
      "removed": true,
      "createdAt": "2023-11-20T15:30:00Z",
      "updatedAt": "2023-11-23T18:00:00Z",
      "completedAt": null,
      "notificationSent": false
    },
    {
      "id": "r9g0h1i2j3",
      "userId": "usr_54321",
      "text": "Поздравить друга с днем рождения",
      "time": "2023-12-05T00:00:00Z",
      "tags": ["праздники"],
      "status": "active",
      "removed": false,
      "createdAt": "2023-11-25T20:10:00Z",
      "updatedAt": "2023-11-25T20:10:00Z",
      "completedAt": null,
      "notificationSent": false
    },
    {
      "id": "r0k1l2m3n4",
      "userId": "usr_67890",
      "text": "Заказать билеты в кино",
      "time": "2023-12-03T19:45:00Z",
      "tags": ["развлечения"],
      "status": "active",
      "removed": false,
      "createdAt": "2023-11-29T21:30:00Z",
      "updatedAt": "2023-11-29T21:30:00Z",
      "completedAt": null,
      "notificationSent": false
    }
  ];
  res.json(reminders);
})



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