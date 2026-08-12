import logging
import requests
from src.job_alert.config import config
from src.job_alert.normalization.schemas import NormalizedJob

logger = logging.getLogger(__name__)

def send_telegram_alert(job: NormalizedJob, score: int, summary: str):
    if not config.prefs.alerts.telegram_enabled or not config.telegram_bot_token or not config.telegram_chat_id:
        return
        
    url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
    
    text = (
        f"🔥 NEW HIGH-PRIORITY ENGINEERING OPPORTUNITY\n\n"
        f"Company: {job.company_name}\n"
        f"Role: {job.title}\n"
        f"Location: {job.location}\n"
        f"Score: {score}/100\n"
        f"Source: {job.source}\n\n"
        f"Why it matches:\n{summary}\n\n"
        f"APPLY: {job.apply_url or job.source_url}"
    )
    
    try:
        requests.post(url, json={"chat_id": config.telegram_chat_id, "text": text}, timeout=10)
        logger.info("Telegram alert sent")
    except Exception as e:
        logger.error(f"Failed to send telegram alert: {e}")
