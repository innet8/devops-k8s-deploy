FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install uwsgi

CMD ["uwsgi", "--http", ":5000", "--wsgi-file", "app.py", "--callable", "app", "--processes", "3", "--threads", "2"]