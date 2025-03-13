-- Использование расширения для генерации UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Создание типов перечислений
CREATE TYPE sex_type AS ENUM ('male', 'female');
CREATE TYPE reminder_status AS ENUM ('active', 'completed', 'forgotten');
CREATE TYPE habit_period AS ENUM ('daily', 'weekly', 'monthly', 'custom');
CREATE TYPE achievement_category AS ENUM ('reminder', 'habit', 'system');
CREATE TYPE image_status AS ENUM ('good', 'neutral', 'bad');

-- Таблица пользователей
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE,
    sex sex_type,
    first_name VARCHAR(255),
    second_name VARCHAR(255),
    birth_date DATE,
    telegram_id VARCHAR(255) UNIQUE,
    calendar_integration_key VARCHAR(255),
    timezone VARCHAR(100) DEFAULT 'UTC',
    level INTEGER DEFAULT 1,
    experience INTEGER DEFAULT 0,
    streak INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создаем индекс для поиска по telegram_id
CREATE INDEX idx_users_telegram_id ON users(telegram_id);

-- Таблица тегов
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#FFFFFF',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

-- Создаем индекс для поиска по user_id
CREATE INDEX idx_tags_user_id ON tags(user_id);

-- Таблица напоминаний
CREATE TABLE reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    status reminder_status DEFAULT 'active',
    removed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    notification_sent BOOLEAN DEFAULT FALSE
);

-- Создаем индексы для частых запросов
CREATE INDEX idx_reminders_user_id ON reminders(user_id);
CREATE INDEX idx_reminders_time ON reminders(time);
CREATE INDEX idx_reminders_status ON reminders(status);
CREATE INDEX idx_reminders_removed ON reminders(removed);

-- Таблица связей между напоминаниями и тегами
CREATE TABLE reminder_tags (
    reminder_id UUID REFERENCES reminders(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (reminder_id, tag_id)
);

-- Таблица привычек
CREATE TABLE habits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    period habit_period NOT NULL,
    custom_period TEXT,
    progress INTEGER DEFAULT 0,
    target INTEGER DEFAULT 1,
    current_streak INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    start_date DATE NOT NULL,
    end_date DATE,
    removed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создаем индексы для привычек
CREATE INDEX idx_habits_user_id ON habits(user_id);
CREATE INDEX idx_habits_start_date ON habits(start_date);
CREATE INDEX idx_habits_removed ON habits(removed);

-- Таблица прогресса привычек
CREATE TABLE habit_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    habit_id UUID NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(habit_id, date)
);

-- Индекс для поиска прогресса по привычке
CREATE INDEX idx_habit_progress_habit_id ON habit_progress(habit_id);
CREATE INDEX idx_habit_progress_date ON habit_progress(date);

-- Таблица достижений (шаблоны ачивок)
CREATE TABLE achievement_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon_url VARCHAR(512),
    condition TEXT NOT NULL,
    category achievement_category NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица пользовательских достижений
CREATE TABLE user_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id UUID NOT NULL REFERENCES achievement_templates(id),
    unlocked BOOLEAN DEFAULT FALSE,
    unlocked_at TIMESTAMP WITH TIME ZONE,
    progress INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, template_id)
);

-- Индексы для таблицы пользовательских достижений
CREATE INDEX idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX idx_user_achievements_unlocked ON user_achievements(unlocked);

-- Таблица нейроизображений
CREATE TABLE neuro_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    habit_id UUID REFERENCES habits(id) ON DELETE SET NULL,
    reminder_id UUID REFERENCES reminders(id) ON DELETE SET NULL,
    image_url VARCHAR(512) NOT NULL,
    thumbnail_url VARCHAR(512),
    prompt TEXT,
    status image_status,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для таблицы нейроизображений
CREATE INDEX idx_neuro_images_user_id ON neuro_images(user_id);
CREATE INDEX idx_neuro_images_habit_id ON neuro_images(habit_id);
CREATE INDEX idx_neuro_images_reminder_id ON neuro_images(reminder_id);

-- Таблица статистики пользователя (кешированные данные)
CREATE TABLE user_statistics (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    reminders_completed INTEGER DEFAULT 0,
    reminders_forgotten INTEGER DEFAULT 0,
    last_calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица ежедневной активности для статистики
CREATE TABLE daily_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    completed_items INTEGER DEFAULT 0,
    UNIQUE(user_id, date)
);

-- Индекс для таблицы ежедневной активности
CREATE INDEX idx_daily_activity_user_id ON daily_activity(user_id);
CREATE INDEX idx_daily_activity_date ON daily_activity(date);

-- Добавление триггеров для автоматического обновления полей updated_at

-- Функция обновления timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для таблицы users
CREATE TRIGGER update_users_modtime
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Триггер для таблицы reminders
CREATE TRIGGER update_reminders_modtime
BEFORE UPDATE ON reminders
FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Триггер для таблицы habits
CREATE TRIGGER update_habits_modtime
BEFORE UPDATE ON habits
FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Триггер для таблицы user_achievements
CREATE TRIGGER update_user_achievements_modtime
BEFORE UPDATE ON user_achievements
FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Добавляем процедуру для обновления последней активности пользователя
CREATE OR REPLACE FUNCTION update_user_last_active()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггеры для обновления активности пользователя
CREATE TRIGGER update_user_activity_on_reminder
AFTER INSERT OR UPDATE ON reminders
FOR EACH ROW EXECUTE FUNCTION update_user_last_active();

CREATE TRIGGER update_user_activity_on_habit
AFTER INSERT OR UPDATE ON habits
FOR EACH ROW EXECUTE FUNCTION update_user_last_active();

CREATE TRIGGER update_user_activity_on_habit_progress
AFTER INSERT OR UPDATE ON habit_progress
FOR EACH ROW EXECUTE FUNCTION update_user_last_active();

-- Создаем индексы для часто используемых запросов на выборку напоминаний
CREATE INDEX idx_reminders_upcoming ON reminders(user_id, time) 
WHERE status = 'active' AND removed = FALSE AND time > CURRENT_TIMESTAMP;

-- Создаем индекс для часто используемых запросов на выборку привычек
CREATE INDEX idx_habits_active ON habits(user_id)
WHERE removed = FALSE;
