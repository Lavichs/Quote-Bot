FROM python:3.12

WORKDIR ./app

RUN apt update
RUN apt install bat -y

COPY config.py config.py
COPY .env .env
COPY alembic.ini alembic.ini

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./migration ./migration
COPY app.py app.py
COPY ./src ./src

CMD ["python", "app.py"]