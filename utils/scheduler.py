from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Scheduler for jobs
scheduler = AsyncIOScheduler()

def get_scheduler():
    return scheduler
