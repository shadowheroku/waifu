from Bot import scheduler, logger
from Bot.handlers.minigames.token_redeem import scheduled_cleanup
from Bot.handlers.users.auction import process_expired_auctions_task
from Bot.handlers.admin.backup import scheduled_backup
from pytz import timezone
from Bot.handlers.users.leaderboard import daily_grab_token_inspection, daily_rewards_handler

def setup_scheduler_tasks():

    scheduler.add_job(scheduled_cleanup,'interval',hours=1,id='redeem_code_cleanup',replace_existing=True)    
    scheduler.add_job(process_expired_auctions_task,'interval',minutes=5,id='process_expired_auctions',replace_existing=True)
    scheduler.add_job(scheduled_backup, "cron", hour=0, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=1, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=2, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=3, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=4, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=5, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=6, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=7, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=8, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=9, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=10, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=11, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=12, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=13, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=14, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=15, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=16, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=17, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=18, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=19, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=20, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=21, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=22, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(scheduled_backup, "cron", hour=23, minute=0, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(daily_grab_token_inspection, "cron", hour=22, minute=00, timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(daily_rewards_handler, "cron", hour=22, minute=00, timezone=timezone("Asia/Kolkata"))
    
    logger.info("Scheduler tasks setup complete")