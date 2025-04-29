const express = require('express');
const session = require('express-session');
const axios = require('axios');
const cookieParser = require('cookie-parser');
const cors = require('cors');


const app = express();
require('dotenv').config();
const PORT = process.env.PORT || 80;
const BACKEND_URL = process.env.BACKEND_URL ||'http://localhost:8000'; // URL вашего бэкенда

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
  cookie: { secure: false } 
}));

app.get('/api/auth/telegram', async (req, res) => {
  try {
    const response = await axios.post(`${BACKEND_URL}/v1/auth/telegram`, req.body);
    req.session.token = response.data; 
    res.redirect('/reminders');
  } catch (error) {
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});
const checkToken = (req, res, next) => {
  if (req.path.startsWith('/css/') || req.path.startsWith('/js/') || req.path.startsWith('/assets/')) {
    return next();
  }
  if (!req.session.token) { 
    if (req.path !== '/telegram') { 
      return res.redirect('/telegram'); 
    }
  }
  next(); 
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
    console.log(req.method);
    console.log(req.body);
    const options = {
      method: req.method,
      url: `${BACKEND_URL}/v1${req.originalUrl.replace('/api', '')}`,
      data: (req.method === 'POST' || req.method === 'PUT') ? req.body : undefined, 
      headers: {
        'Authorization': `Bearer ${req.session.token}`,
        'Content-Type': 'application/json' 
      },
    };
    const response = await axios(options);
    res.status(response.status).json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});

app.use(express.static('public'));

app.listen(PORT, () => {
  console.log(`Node.js proxy server running on http://localhost:${PORT}`);
});