FROM python:3.9-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cron_scheduler.py .

# Niet-root user (veiligheid)
RUN useradd -m -u 1000 scheduler && chown -R scheduler:scheduler /app
USER scheduler

CMD ["python", "-u", "cron_scheduler.py"]