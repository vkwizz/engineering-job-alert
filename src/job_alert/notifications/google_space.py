import logging
import requests
from typing import Optional
from src.job_alert.config import config
from src.job_alert.normalization.schemas import NormalizedJob

logger = logging.getLogger(__name__)

def send_google_space_alert(job: NormalizedJob, score: int, summary: str) -> bool:
    webhook_url = config.google_space_webhook_url
    if not webhook_url:
        return False

    payload = {
        "cardsV2": [
            {
                "cardId": f"job_alert_{job.canonical_key}",
                "card": {
                    "header": {
                        "title": f"{job.title}",
                        "subtitle": f"🏢 {job.company_name} | Match Score: {score}/100",
                        "imageUrl": "https://cdn-icons-png.flaticon.com/512/3858/3858686.png",
                        "imageType": "CIRCLE"
                    },
                    "sections": [
                        {
                            "header": "Opportunity Details",
                            "widgets": [
                                {
                                    "decoratedText": {
                                        "topLabel": "Location",
                                        "text": f"📍 {job.location or 'Not specified'}"
                                    }
                                },
                                {
                                    "decoratedText": {
                                        "topLabel": "Source",
                                        "text": f"🔗 {job.source}"
                                    }
                                },
                                {
                                    "textParagraph": {
                                        "text": f"<b>Why it matches:</b><br>{summary}"
                                    }
                                },
                                {
                                    "buttonList": {
                                        "buttons": [
                                            {
                                                "text": "Apply Now →",
                                                "onClick": {
                                                    "openLink": {
                                                        "url": job.apply_url or job.source_url
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"Google Space notification sent for '{job.title}'")
            return True
        else:
            logger.error(f"Google Space webhook error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send Google Space notification: {e}")
        return False
