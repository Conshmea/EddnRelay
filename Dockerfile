FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 9600

ENV PYTHONPATH=/app
CMD ["python", "src/application.py"]
