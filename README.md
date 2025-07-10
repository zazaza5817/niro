# 🚀 NiroVPN - Secure VPN Service

![NiroVPN Logo](https://img.shields.io/badge/NiroVPN-Secure%20Connection-blue?style=for-the-badge)

**NiroVPN** - это современный VPN сервис, обеспечивающий быстрое, надежное и приватное подключение к интернету. Мы гарантируем полную конфиденциальность данных и не ведем логи активности пользователей.

## ✨ Особенности

- 🔒 **Полная конфиденциальность** - никакие пользовательские данные не собираются
- ⚡ **Высокая скорость** подключения 
- 🌍 **Кросс-платформенность** - используйте подписку на любых устройствах
- 🎁 **Реферальная система** с кастомными планами и скидками
- 💳 **Удобная оплата** через Telegram Stars
- ⚙️ **Простая настройка** в несколько кликов

## 🛠 Архитектура проекта

```
├── backend/               # FastAPI сервер
│   ├── models/            # Pydantic модели
│   ├── routers/           # API роуты
│   ├── services/          # Бизнес-логика
│   └── main.py            # Главный файл приложения
├── telegram_bot/          # Telegram бот
├── db_init/               # SQL скрипты для БД
├── settings/              # Конфигурация планов
├── frontend/              # React фронтенд
├── monitoring/            # Конфигурация графаны
└── docker-compose.yml     # Docker конфигурация
```


## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd nirovpn
```

### 2. Настройка переменных окружения
```.env
# Отредактируйте .env файл с вашими настройками
# PostgreSQL настройки
POSTGRES_DB=vpn_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
DATABASE_URL=postgresql://user:password@db:5432/vpn_db

# Пути и секретные ключи
JWT_SECRET_KEY=jwt
TG_TOKEN=tg
TG_BOT_USERNAME=nirovpnbot

# Настройки бэкенда
DEBUG=0

GRAFANA_USER=grafana_user
GRAFANA_PASSWORD=grafana_password

INTERNAL_API_KEY=apikey

API_BASE_URL=http://backend:8000

```

### 3. Запуск через Docker
```bash
docker-compose up -d
```

## 💾 База данных

Проект использует PostgreSQL с следующими основными таблицами:

- `users` - пользователи системы
- `referral_codes` - реферальные коды
- `referral_usage` - использование кодов пользователями
- `referral_plans` - планы подписки для кодов

## 🔧 Конфигурация

### Планы подписки (plans.json)
```json
{
    "1month": {
        "price": 150,
        "duration": 30,
        "title": "Подписка на месяц",
        "description": "Действует 30 дней",
        "price_per_month": 150
    }
}
```

## 🛡 Безопасность

- Все внутренние API защищены ключом авторизации
- Telegram WebApp аутентификация для пользовательских запросов
- Валидация данных через Pydantic модели
- Защита от SQL инъекций через параметризованные запросы

## 🤝 Наши контакты
- 💬 **Telegram**: [@nirovpnbot](https://t.me/nirovpnbot)
- 🌐 **Website**: https://nirovpn.com
