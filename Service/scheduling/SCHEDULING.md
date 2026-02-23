# Fantasy F1 - Scheduling Job in Production

## Locale (Development)

Avvia lo scheduler:
```bash
cd Service/schedule
python scheduler.py
```

Job gira ogni domenica alle 20:00 (orario server).

Oppure esegui il job una volta per testare:
```bash
cd Service/schedule
python scoring_job.py
```

---

## Production - Opzioni

### 1️⃣ **Heroku / Railway / Render**
Questi servizi supportano "one-off dynos" (job schedulati).

**Crea `Procfile`:**
```
web: gunicorn app:app
worker: python scheduler.py
```

**Deploy e configura:**
- Heroku: `heroku ps:scale worker=1`
- Railway/Render: aggiungi il servizio tramite UI

---

### 2️⃣ **VPS Linux (AWS, DigitalOcean, Linode, ecc.)**

#### Opzione A: Cron Job
Aggiungi al crontab:
```bash
crontab -e
```

```cron
# Domenica alle 20:00 (CEST / UTC+2)
0 20 * * 0 cd /path/to/FantasyF1/Service/schedule && /usr/bin/python3 scoring_job.py
```

#### Opzione B: Systemd Timer (consigliato)

1. Crea `/etc/systemd/system/fantasy-f1-scoring.service`:
```ini
[Unit]
Description=Fantasy F1 Scoring Job
After=network.target

[Service]
Type=oneshot
ExecStart=/path/to/venv/bin/python /path/to/Service/schedule/scoring_job.py
WorkingDirectory=/path/to/Service/schedule
User=www-data

[Install]
WantedBy=multi-user.target
```

2. Crea `/etc/systemd/system/fantasy-f1-scoring.timer`:
```ini
[Unit]
Description=Run Fantasy F1 Scoring Job every Sunday at 20:00
Requires=fantasy-f1-scoring.service

[Timer]
# Domenica alle 20:00
OnCalendar=Sun *-*-* 20:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

3. Abilita:
```bash
sudo systemctl daemon-reload
sudo systemctl enable fantasy-f1-scoring.timer
sudo systemctl start fantasy-f1-scoring.timer
```

4. Verifica:
```bash
sudo systemctl list-timers
sudo journalctl -u fantasy-f1-scoring.service -f
```

---

### 3️⃣ **Docker**

Nel tuo `docker-compose.yml`:
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    command: gunicorn app:app

  scheduler:
    build: .
    working_dir: /app/schedule
    command: python scheduler.py
    depends_on:
      - db
```

---

### 4️⃣ **Windows Server / Task Scheduler**

1. Crea script batch `scoring_job.bat`:
```batch
@echo off
cd C:\path\to\Service\schedule
python scoring_job.py
```

2. Apri Task Scheduler → Crea task:
   - **Trigger**: Domenica alle 20:00
   - **Action**: Esegui `scoring_job.bat`
   - **User**: Sistema (SYSTEM)

---

## 📊 Monitoraggio

Aggiungi logging per tracciare gli esecuzioni (in `schedule/scoring_job.py`):

```python
import logging

logging.basicConfig(
    filename='scoring.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info(f"Job avviato: {datetime.now()}")
```

I log saranno salvati in `Service/schedule/scoring.log`

---

## 🔄 Alternative (Future)

- **APScheduler con persistent storage**: salva stato della schedulazione su DB
- **Celery + Redis**: per job ancora più complessi
- **GitHub Actions**: esegui manualmente o su schedule gratuito

---

## Troubleshooting

- **Job non parte**: Verifica timezone del server (`date -R` su Linux)
- **Errore DB**: Assicurati che il database sia raggiungibile
- **Ergast API down**: Script fallisce gracefully, riprova successivamente
