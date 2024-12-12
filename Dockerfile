# Используем минимальный образ Python
FROM python:3.12-slim
#LABEL authors="goit-hw-web-14"
# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем git для клонирования репозитория
RUN apt-get update && apt-get install -y git

# Копируем файлы проекта в контейнер
COPY . /app

# Клонируем проект из GitHub в контейнер
#RUN git clone https://github.com/your-username/your-repository.git .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Открываем порт для приложения
EXPOSE 8000

# Запуск приложения
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]

#CMD alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000