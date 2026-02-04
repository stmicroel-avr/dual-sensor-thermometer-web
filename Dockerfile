FROM python:3.14-alpine
LABEL authors="stmicroel"

WORKDIR /WORKDIR /usr/src/app

COPY requirements-linux.txt ./
RUN pip install -r requirements-linux.txt

COPY app .

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]