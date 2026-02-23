"""
Fantasy F1 Scheduler
Schedula il job di scoring per domenica sera
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from scoring_job import run_scoring_job
import atexit

def start_scheduler():
    """Avvia lo scheduler in background"""
    scheduler = BackgroundScheduler()
    
    # Domenica sera alle 20:00 (dopo la gara F1)
    scheduler.add_job(
        func=run_scoring_job,
        trigger=CronTrigger(day_of_week=6, hour=20, minute=0),  # 6 = domenica
        id='fantasy_f1_scoring',
        name='Fantasy F1 Scoring Job',
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ Scheduler avviato: job eseguito ogni domenica alle 20:00")
    
    # Shutdown properly on exit
    atexit.register(lambda: scheduler.shutdown())
    
    return scheduler

if __name__ == '__main__':
    start_scheduler()
    import time
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("\n⛔ Scheduler stoppato")
