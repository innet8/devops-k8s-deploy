FROM python:3.10-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install uwsgi

CMD ["uwsgi", "--ini", "/app/uwsgi.ini"]