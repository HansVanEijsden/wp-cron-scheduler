# wp-cron-scheduler
Een complete Docker-gebaseerde oplossing die WordPress-cronjobs uitvoeringen spreidt. In plaats van een vaste crontab gebruiken we een Python-scheduler in een container die voor elke site een eigen interval en een slimme jitter toepast. De configuratie gebeurt via een eenvoudig JSON-bestand dat je per site kunt aanpassen.
