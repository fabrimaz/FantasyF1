# Schedule Module

Job di scoring ricorrente per Fantasy F1.

## File

- `__init__.py` - Modulo Python
- `scoring_job.py` - Job principale (scarica risultati da Ergast, calcola punteggi)
- `scheduler.py` - Scheduler APScheduler (esegue il job ogni domenica alle 20:00)

## Uso Locale

```bash
# Esegui il job una volta
python scoring_job.py

# Esegui lo scheduler (runs job ogni domenica sera)
python scheduler.py
```

## Production

Vedi [SCHEDULING.md](../SCHEDULING.md) per configurare in ambienti production (Heroku, VPS, Docker, Windows Server).
