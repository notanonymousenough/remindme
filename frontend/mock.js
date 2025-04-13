
const express = require('express');
const session = require('express-session');
const axios = require('axios');
const cookieParser = require('cookie-parser');
const cors = require('cors');


const app = express();
app.use(express.json());

app.post('/v1/auth/telegram', async (req, res) => {
    res.json("{'access_token': '...'}")
});

const habits=[
    {
    "id": "habit_12345",
    "userId": "user_67890",
    "text": "Отжимания",
    "interval": "daily",
    "custom_interval": "string",
    "currentStreak": 3,
    "status": "active",
    "progress": [   
        ["2025-04-01", true ],
        ["2025-04-02", true ],
        ["2025-04-03", false ],
        ["2025-04-04", true ],
        ["2025-04-05", false ],
        ["2025-04-06", true ],
        ["2025-04-07", true ],
        ["2025-04-08", false ],
        ["2025-04-09", true ],
        ["2025-04-10", true ],
        ["2025-04-11", true ],
        ["2025-04-12", true ],
        ["2025-04-13", false ],
    ],
    "bestStreak": 3,
    "startDate": "2025-03-31",
    "endDate": "2025-04-13",
    "removed": false,
    "createdAt": "2023-09-01T12:00:00Z",
    "updatedAt": "2023-10-01T12:00:00Z"
  },
  {
    "id": "habit_12344",
    "userId": "user_67890",
    "text": "Бег",
    "interval": "daily",
    "custom_interval": "string",
    "currentStreak": 3,
    "status": "active",
    "progress": [   
        ["2025-03-02", false ],
        ["2025-03-03", true ],
        ["2025-03-04", true ],
        ["2025-03-05", true ],
        ["2025-03-06", false ],
        ["2025-03-07", true ],
        ["2025-03-08", true ],
        ["2025-03-09", false ],
        ["2025-03-10", false ],
    ],
    "bestStreak": 3,
    "startDate": "2025-03-02",
    "endDate": "2025-03-10",
    "removed": false,
    "createdAt": "2023-09-01T12:00:00Z",
    "updatedAt": "2023-10-01T12:00:00Z"
  }
];
const reminders = [
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

const achievement = [
    {
        "id": "r0k1l2m3n4",
        "userId": "usr_67890",
        "description": "&#127942 Выполненно 10 напоминаний",
        "unlockedAt": "2023-12-03T19:45:00Z"
    },
    {
        "id": "r0k1l2m3n4",
        "userId": "usr_67890",
        "description": "&#127942 5 раз подряд соблюдать привычки",
        "unlockedAt": "2023-12-03T19:45:00Z"
    }
];

const statistics=[
    {
        "userId": "usr_67890",
        "remindersCompleted": 0,
        "remindersForgotten": 0,
        "lastReset": 0
    }
];

app.post('/v1/reminders', (req, res) => {
    req.body.id= (Math.random(100000000)).toString();
    req.body.userId='usr_67890';
    const reminderData = req.body;
    reminders.push(reminderData);
});

app.get('/v1/reminders', (req, res) => {
    const now = new Date();
    const today = now.toISOString().split('T')[0];

    statistics.forEach(stat => {
        if (stat.lastReset !== today) {
            stat.remindersCompleted = 0; 
            stat.remindersForgotten = 0;  
            stat.lastReset = today; 
        }
    });

    reminders.forEach(reminder => {
        if (reminder.time && !isNaN(new Date(reminder.time))) {
            const reminderDate = new Date(reminder.time).toISOString().split('T')[0];
            if (today === reminderDate) {
                if (reminder.status === 'completed' && !reminder.alreadyCounted) {
                    const userStats = statistics.find(stat => stat.userId === reminder.userId);
                    if (userStats) {
                        userStats.remindersCompleted++;
                        reminder.alreadyCounted = true;
                    }
                } 
                else if (reminder.status !== 'completed') {
                    const reminderTime = new Date(reminder.time);
                    if (reminderTime <= now && !reminder.alreadyCounted) {
                        reminder.status = 'forgotten';
                        const userStats = statistics.find(stat => stat.userId === reminder.userId);
                        if (userStats) {
                            userStats.remindersForgotten++;
                            reminder.alreadyCounted = true; 
                        }
                    }
                }
                
            }
            if (reminder.status !== 'completed') {
                const reminderTime = new Date(reminder.time);
                if (reminderTime <= now) {
                    reminder.status = 'forgotten';
                    const userStats = statistics.find(stat => stat.userId === reminder.userId);
                    if (userStats) {
                        reminder.alreadyCounted = true;
                    }
                }
            }
        }
    });
    res.json(reminders);
});

app.get('/v1/habits', (req, res) => {
    res.json(habits);
});
app.get('/v1/habits/:habitId', (req, res) => {
    const habitId = req.params.habitId;
    const habit = habits.find(h => h.id === habitId);
    if (habit) {
        res.json(habit);
    } else {
        res.status(404).send('Привычка не найдена');
    }
});

app.get('/v1/achievement', (req, res) => {
    res.json(achievement);
});
app.get('/v1/progress', (req, res) => {
    res.json(statistics);
});

app.put('/v1/reminders/:reminderId/complete', (req, res) => {
    const reminderId = req.params.reminderId;
    const { status } = req.body;
    const reminder = reminders.find(r => r.id === reminderId);
    if (reminder) {
        reminder.status = status; 
        reminder.updatedAt = new Date().toISOString(); 
        if (status === "completed") {
            reminder.completedAt = new Date().toISOString(); 
        }
        res.json(reminder);
    } else {
        res.status(404).json({ error: 'Напоминание не найдено' });
    }
});
app.put('/v1/habits/:habitId/complete', (req, res) => {
    const habitId = req.params.habitId;
    const { status } = req.body; 
    const habit = habits.find(r => r.id === habitId);
    if (habit) {
        habit.status = status; 
        habit.updatedAt = new Date().toISOString(); 
        if (status === "completed") {
            habit.completedAt = new Date().toISOString();
        }
        const today = new Date().toISOString().split('T')[0]; 
        const entry = habit.progress.find(p => p[0] === today);
        if (entry && entry[1] === false) {
            entry[1] = true; 
        }
        res.json(habit);
    } else {
        res.status(404).json({ error: 'Напоминание не найдено' });
    }
});

app.put('/v1/reminders/:reminderId', (req, res) => {
    const id = req.params.reminderId;
    const updatedData = req.body;    
    const index = reminders.findIndex(reminder => reminder.id === id);
    if (index !== -1) {
        reminders[index].text = updatedData.text || reminders[index].text; 
        reminders[index].time = updatedData.time || reminders[index].time; 
        return res.status(200).json({ success: true, updatedReminder: reminders[index] });
    } else {
        return res.status(404).json({ success: false, message: 'Напоминание не найдено.' });
    }
});

app.delete('/v1/habits/:habitId', (req, res) => {
    const id = req.params.habitId;
    const index = habits.findIndex(habit => habit.id === id);
    if (index !== -1) {
        habits.splice(index, 1); 
        return res.status(200).json({ success: true, message: 'Напоминание успешно удалено.' });
    } else {
        return res.status(404).json({ success: false, message: 'Напоминание не найдено.' });
    }
});

app.delete('/v1/reminders/:reminderId', (req, res) => {
    const id = req.params.reminderId;
    const index = reminders.findIndex(reminder => reminder.id === id);
    if (index !== -1) {
        reminders.splice(index, 1); 
        return res.status(200).json({ success: true, message: 'Напоминание успешно удалено.' });
    } else {
        return res.status(404).json({ success: false, message: 'Напоминание не найдено.' });
    }
});

app.use(express.static('public'));

app.listen(8000, () => {
  console.log(`Node.js proxy server running on http://localhost:8000`);
});