FROM python:3.14-alpine
LABEL authors="stmicroel"

WORKDIR /usr/src/app

COPY requirements-linux.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app .

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]