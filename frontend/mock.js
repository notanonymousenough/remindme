
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
    "progress": 5,
    "target": 7,
    "currentStreak": 3,
    "bestStreak": 10,
    "startDate": "2023-09-01",
    "endDate": "2023-12-01",
    "removed": false,
    "createdAt": "2023-09-01T12:00:00Z",
    "updatedAt": "2023-10-01T12:00:00Z"
  }];
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

app.post('/v1/reminders', (req, res) => {
    const reminderData = req.body;
    reminders.push(reminderData);
});

// Если вы хотите получить все локальные напоминания, добавьте этот маршрут
app.get('/v1/reminders', (req, res) => {
  res.json(reminders);
});
app.get('/v1/habits', (req, res) => {
    res.json(habits);
  });


app.put('/v1/reminders/:id/status', (req, res) => {
    const reminderId = req.params.id;
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

app.put('/v1/reminders/:id', (req, res) => {
    const id = req.params.id;
    const updatedData = req.body;
    console.log(req.body);    
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

app.delete('/v1/reminders/:id', (req, res) => {
    const id = req.params.id;

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