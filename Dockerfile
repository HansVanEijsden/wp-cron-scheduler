FROM python:3.14-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cron_scheduler.py .

# Non-root user (safety)
RUN useradd -m -u 1000 scheduler && chown -R scheduler:scheduler /app
USER scheduler

CMD ["python", "-u", "cron_scheduler.py"]
