
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
    "period": "daily",
    "customPeriod": null,
    "status": "active",
    "progress": 6,
    "target": 7,
    "currentStreak": 3,
    "customPeriod": [   '2025-04-01T12:00:00Z',
                        '2025-04-02T12:00:00Z',
                        '2025-04-04T12:00:00Z',
                        '2025-04-05T12:00:00Z',
                        '2025-04-06T12:00:00Z',
                        '2025-04-08T12:00:00Z',
                    ],
    "bestStreak": 3,
    "startDate": "2025-04-01",
    "endDate": "2025-04-09",
    "removed": false,
    "createdAt": "2023-09-01T12:00:00Z",
    "updatedAt": "2023-10-01T12:00:00Z"
  },
  {
    "id": "habit_12344",
    "userId": "user_67890",
    "text": "Бег",
    "period": "daily",
    "status": "active",
    "customPeriod": null,
    "progress": 6,
    "target": 7,
    "currentStreak": 3,
    "customPeriod": [   '2025-03-01T12:00:00Z',
                        '2025-03-02T12:00:00Z',
                        '2025-03-03T12:00:00Z',
                        '2025-03-05T12:00:00Z',
                        '2025-03-06T12:00:00Z',
                        '2025-03-09T12:00:00Z',
                    ],
    "bestStreak": 3,
    "startDate": "2025-03-01",
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
        "remindersForgotten": 0
    }
];

app.post('/v1/reminders', (req, res) => {
    req.body.id= (Math.random(100000000)).toString();
    req.body.userId='usr_67890';
    const reminderData = req.body;
    reminders.push(reminderData);
});

// Если вы хотите получить все локальные напоминания, добавьте этот маршрут
app.get('/v1/reminders', (req, res) => {
    const now = new Date();

    reminders.forEach(reminder => {
        // Увеличиваем счетчик remindersCompleted для уже завершенных напоминаний
        if (reminder.status === 'completed' && !reminder.alreadyCounted) {
            const userStats = statistics.find(stat => stat.userId === reminder.userId);
            if (userStats) {
                userStats.remindersCompleted++;
                reminder.alreadyCounted = true; // Отмечаем, что мы уже учитывали это напоминание
            }
        } 
        // Проверяем дату только для напоминаний со статусом не completed
        else if (reminder.status !== 'completed') {
            const reminderTime = new Date(reminder.time);
            if (reminderTime <= now && !reminder.alreadyCounted) {
                // Меняем статус на forgotten
                reminder.status = 'forgotten';
                const userStats = statistics.find(stat => stat.userId === reminder.userId);
                if (userStats) {
                    userStats.remindersForgotten++;
                    reminder.alreadyCounted = true; // Отмечаем, что мы уже учитывали это напоминание
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
    const { status } = req.body; // Ожидаем, что статус будет передан в теле запроса
    const reminder = reminders.find(r => r.id === reminderId);

    if (reminder) {
        reminder.status = status; // Обновление статуса
        reminder.updatedAt = new Date().toISOString(); // Обновление времени изменения
        if (status === "completed") {
            reminder.completedAt = new Date().toISOString(); // Устанавливаем время завершения, если статус completed
        }
        res.json(reminder); // Возвращаем обновленное напоминание
    } else {
        res.status(404).json({ error: 'Напоминание не найдено' });
    }
});
app.put('/v1/habits/:habitId/complete', (req, res) => {
    const habitId = req.params.habitId;
    const { status } = req.body; // Ожидаем, что статус будет передан в теле запроса
    const habit = habits.find(r => r.id === habitId);

    if (habit) {
        habit.status = status; // Обновление статуса
        habit.updatedAt = new Date().toISOString(); // Обновление времени изменения
        if (status === "completed") {
            habit.completedAt = new Date().toISOString(); // Устанавливаем время завершения, если статус completed
        }
        res.json(habit); // Возвращаем обновленное напоминание
    } else {
        res.status(404).json({ error: 'Напоминание не найдено' });
    }
});

app.put('/v1/reminders/:reminderId', (req, res) => {
    const id = req.params.reminderId;
    const updatedData = req.body;    
    // Находим индекс напоминания по ID
    const index = reminders.findIndex(reminder => reminder.id === id);

    // Если напоминание найдено, обновляем его
    if (index !== -1) {
        reminders[index].text = updatedData.text || reminders[index].text; // Сохраняем старое значение, если новое не передано
        reminders[index].time = updatedData.time || reminders[index].time; // Сохраняем старое значение, если новое не передано
        return res.status(200).json({ success: true, updatedReminder: reminders[index] });
    } else {
        // Если напоминание не найдено, возвращаем ошибку
        return res.status(404).json({ success: false, message: 'Напоминание не найдено.' });
    }
});

app.delete('/v1/habits/:habitId', (req, res) => {
    const id = req.params.habitId;
    // Находим индекс напоминания по ID
    const index = habits.findIndex(habit => habit.id === id);

    // Если напоминание найдено, удаляем его
    if (index !== -1) {
        habits.splice(index, 1); // Удаляем напоминание из массива
        return res.status(200).json({ success: true, message: 'Напоминание успешно удалено.' });
    } else {
        // Если напоминание не найдено, возвращаем ошибку
        return res.status(404).json({ success: false, message: 'Напоминание не найдено.' });
    }
});

app.delete('/v1/reminders/:reminderId', (req, res) => {
    const id = req.params.reminderId;

    // Находим индекс напоминания по ID
    const index = reminders.findIndex(reminder => reminder.id === id);

    // Если напоминание найдено, удаляем его
    if (index !== -1) {
        reminders.splice(index, 1); // Удаляем напоминание из массива
        return res.status(200).json({ success: true, message: 'Напоминание успешно удалено.' });
    } else {
        // Если напоминание не найдено, возвращаем ошибку
        return res.status(404).json({ success: false, message: 'Напоминание не найдено.' });
    }
});



/*app.post('/v1/reminders', (req, res) => {
    console.log("Сработало!")
    res.json({
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
        })
});
app.get('/v1/reminders', function(req, res) {
    
    res.json(reminders);
});
*/
app.use(express.static('public'));

app.listen(8000, () => {
  console.log(`Node.js proxy server running on http://localhost:8000`);
});