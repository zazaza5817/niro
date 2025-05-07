# Этап сборки
FROM node:20-alpine

WORKDIR /app

# Копируем package.json и package-lock.json
COPY package*.json ./

# Устанавливаем зависимости
RUN npm ci

# Это заставит Docker игнорировать кэш при каждой сборке
ARG CACHE_BUST=$(date +%s)

# Копируем исходный код
COPY . .

# Собираем приложение
RUN npm run build

# После сборки не завершаем работу контейнера, а ждем
CMD ["sh", "-c", "echo 'Frontend build completed. Files are in /app/dist.' && tail -f /dev/null"]