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
    const response = await axios.post(`${BACKEND_URL}/api/auth/telegram`, req.body);
    req.session.token = response.data.access_token; // Сохраняем токен в сессии
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

const reminders = [];

/*app.post('/api/reminders', async (req, res) => {
  if (!req.session.token) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    const reminderData = req.body; // Ожидаем, что в теле запроса будут данные напоминания
    console.log(req.body);
    reminders.push(reminderData);
    const config = {
      method: 'POST',
      url: `${BACKEND_URL}/api/reminders`, // URL бэкенда для сохранения напоминаний
      headers: {
        'Authorization': `Bearer ${req.session.token}`,
        'Content-Type': 'application/json'
      },
      data: reminderData
    };
    
    const response = await axios(config);
    //res.status(response.status).json(response.data);
    
  } catch (error) {
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});*/

//Изменение маршрута на v1
/*app.use('/api/reminders', async (req, res) => {
  if (!req.session.token) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const url = `${BACKEND_URL}/v1/reminders`;
  console.log(`Redirecting request from ${req.originalUrl} to ${url}`);
  try {
    const config = {
      method: req.method,
      url: url, // Измените URL на BACKEND_URL/v1/reminders
      headers: {
        'Authorization': `Bearer ${req.session.token}`,
        'Content-Type': req.method === 'POST' ? 'application/json' : undefined
      },
      data: req.method === 'POST' ? req.body : undefined // Отправляем данные только для POST-запроса
    }
    const response = await axios(config);
    res.status(response.status).json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({ error: error.message });
  }
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
});*/



app.use('/api/*', async (req, res) => {
  if (!req.session.token) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    //res.json(reminders);
    // Заменяем /api на /v1 в URL
    //const newUrl = `${BACKEND_URL}/v1${req.originalUrl.replace('/api', '')}`;
   // const reminderData = req.body;

    const config = {
      method: req.method,
      //url: newUrl,
      url: `${BACKEND_URL}${req.originalUrl}`,
      headers: {
        'Authorization': `Bearer ${req.session.token}`,
        'Content-Type': 'application/json'
      },
  // Проверьте данные, чтобы убедиться, что они корректны
  // Добавляем новое напоминание в локальное хранилище
      
      data: req.method === 'POST' ? req.body : undefined
    };
    //reminders.push(reminderData)
    const response = await axios(config);
    //console.log(req.method);
    //console.log(req.body);
    res.status(response.status).json(response.data);
    
  } catch (error) {
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});

/*app.get('/api/token', async (req, res) => {
  if (!req.session.token) {
      return res.status(401).json({ error: 'Unauthorized' });
  }
  res.json({ token: req.session.token });
});*/


/*const reminders = [];

app.post('/temp', (req, res) => {
  const reminderData = req.body;
  // Проверьте данные, чтобы убедиться, что они корректны
  // Добавляем новое напоминание в локальное хранилище
  reminders.push(reminderData);
});

// Если вы хотите получить все локальные напоминания, добавьте этот маршрут
app.get('/temp', (req, res) => {
  res.json(reminders);
});*/


// Отдача статических файлов
app.use(express.static('public'));

app.listen(PORT, () => {
  console.log(`Node.js proxy server running on http://localhost:${PORT}`);
});