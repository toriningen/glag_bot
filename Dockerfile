FROM python:3.12

RUN pip install -U pip

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "-m", "app"]
