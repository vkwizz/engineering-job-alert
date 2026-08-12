import logging
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from src.job_alert.config import config

logger = logging.getLogger(__name__)

def render_single_alert_html(job, score: int, summary: str) -> str:
    score_color = "#10b981" if score >= 85 else "#f59e0b" if score >= 70 else "#6b7280"
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f6f8; margin: 0; padding: 20px; }}
        .card {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        .badge {{ display: inline-block; background-color: {score_color}; color: white; font-weight: bold; padding: 6px 12px; border-radius: 20px; font-size: 14px; }}
        .title {{ color: #1e293b; font-size: 20px; margin: 12px 0 4px 0; font-weight: 700; }}
        .company {{ color: #64748b; font-size: 16px; margin-bottom: 16px; }}
        .meta-table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
        .meta-table td {{ padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
        .meta-label {{ color: #64748b; font-weight: 600; width: 120px; }}
        .meta-value {{ color: #0f172a; }}
        .reasoning {{ background-color: #f8fafc; border-left: 4px solid #3b82f6; padding: 12px 16px; border-radius: 4px; margin: 16px 0; color: #334155; font-size: 14px; line-height: 1.5; }}
        .btn {{ display: inline-block; background-color: #2563eb; color: #ffffff !important; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; text-align: center; margin-top: 12px; }}
        .footer {{ text-align: center; color: #94a3b8; font-size: 12px; margin-top: 24px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <span class="badge">Match Score: {score}/100</span>
        <h2 class="title">{job.title}</h2>
        <div class="company">🏢 {job.company_name}</div>
        
        <table class="meta-table">
          <tr>
            <td class="meta-label">📍 Location</td>
            <td class="meta-value">{job.location or 'Not specified'}</td>
          </tr>
          <tr>
            <td class="meta-label">🔗 Source</td>
            <td class="meta-value">{job.source}</td>
          </tr>
          <tr>
            <td class="meta-label">🎯 Match Status</td>
            <td class="meta-value">Verified Target Opportunity</td>
          </tr>
        </table>

        <div class="reasoning">
          <strong>Why this role matches your profile:</strong><br>
          {summary}
        </div>

        <a href="{job.apply_url or job.source_url}" class="btn" target="_blank">Apply Now →</a>
        
        <div class="footer">
          Sent by Personal Engineering Opportunity Intelligence Agent
        </div>
      </div>
    </body>
    </html>
    """

def render_digest_html(jobs_data: List[Dict[str, Any]]) -> str:
    items_html = ""
    for item in jobs_data:
        job = item['job']
        score = item['score']
        summary = item['summary']
        score_color = "#10b981" if score >= 85 else "#f59e0b" if score >= 70 else "#6b7280"
        items_html += f"""
        <div style="border-bottom: 1px solid #e2e8f0; padding: 16px 0;">
          <span style="background-color: {score_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">{score}/100</span>
          <h3 style="margin: 8px 0 4px 0; color: #0f172a;">{job.title}</h3>
          <p style="margin: 0 0 8px 0; color: #475569; font-size: 14px;"><strong>{job.company_name}</strong> • 📍 {job.location or 'India'}</p>
          <p style="margin: 0 0 12px 0; color: #334155; font-size: 13px; background: #f8fafc; padding: 8px; border-radius: 4px;">{summary}</p>
          <a href="{job.apply_url or job.source_url}" style="color: #2563eb; text-decoration: none; font-weight: 600; font-size: 14px;">Apply on {job.source} →</a>
        </div>
        """
        
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 20px;">
      <div style="max-width: 650px; margin: 0 auto; background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <h2 style="color: #0f172a; margin-top: 0;">🚀 Daily Opportunity Intelligence Digest</h2>
        <p style="color: #64748b;">Here are today's top newly discovered engineering roles matching your target criteria:</p>
        {items_html}
        <div style="text-align: center; color: #94a3b8; font-size: 12px; margin-top: 24px;">
          Engineering Opportunity Intelligence Agent
        </div>
      </div>
    </body>
    </html>
    """

def send_email_smtp(subject: str, html_content: str, recipient: str) -> bool:
    sender = config.gmail_sender or config.smtp_username
    if not sender or not config.smtp_password:
        logger.warning("SMTP credentials not fully configured (GMAIL_SENDER_ADDRESS / SMTP_PASSWORD missing)")
        return False
        
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        msg.attach(MIMEText(html_content, "html"))
        
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
            server.starttls()
            server.login(config.smtp_username or sender, config.smtp_password)
            server.sendmail(sender, [recipient], msg.as_string())
            
        logger.info(f"Email alert sent successfully via SMTP to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email via SMTP: {e}")
        return False

def send_gmail_alert(job, score: int, summary: str) -> bool:
    if not config.prefs.alerts.gmail_enabled:
        logger.info("Gmail alerts are disabled in user preferences")
        return False

    recipient = config.gmail_recipient or config.gmail_sender
    if not recipient:
        logger.warning("No recipient configured for Gmail alert")
        return False

    subject = f"🎯 Job Match ({score}/100): {job.title} at {job.company_name}"
    html_content = render_single_alert_html(job, score, summary)
    
    # Try SMTP sending
    return send_email_smtp(subject, html_content, recipient)

def send_digest_email(jobs_data: List[Dict[str, Any]]) -> bool:
    if not config.prefs.alerts.gmail_enabled or not jobs_data:
        return False

    recipient = config.gmail_recipient or config.gmail_sender
    if not recipient:
        return False

    subject = f"📬 Daily Engineering Opportunity Digest ({len(jobs_data)} new roles)"
    html_content = render_digest_html(jobs_data)
    return send_email_smtp(subject, html_content, recipient)
