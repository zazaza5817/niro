# Шаг 1: Используем официальный образ Node.js
FROM node:18-alpine

# Шаг 2: Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Шаг 3: Копируем package.json и package-lock.json для установки зависимостей
COPY package*.json ./

# Шаг 4: Устанавливаем зависимости
RUN npm install

# Шаг 5: Копируем весь проект в контейнер
COPY . .

# Шаг 6: Открываем порт для разработки
EXPOSE 3000

# Шаг 7: Устанавливаем nodemon для автоматической перезагрузки приложения при изменении файлов (опционально)
RUN npm install -g nodemon

# Шаг 8: Команда запуска приложения в режиме разработки
CMD ["npm", "start"]