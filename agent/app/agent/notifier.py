import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from ..models import TriageReport, AlertInfo
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _format_email_body(alert: AlertInfo, report: TriageReport) -> str:
    remediation_steps = "\n".join(
        f"  {i+1}. {step}"
        for i, step in enumerate(report.remediation)
    )
    escalate_str = "YES — escalate to on-call" if report.escalate else "No"

    return f"""
KubeTriage Incident Report
==========================

Incident:     {alert.alertname}
Namespace:    {alert.namespace}
Pod:          {alert.pod}
Container:    {alert.container}
Reason:       {alert.reason or 'N/A'}
Detected:     {alert.received_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

Category:     {report.category}
Root cause:   {report.root_cause}

Remediation:
{remediation_steps}

Suggested command:
  $ {report.kubectl_command}

Escalate:     {escalate_str}

--
Sent by KubeTriage
""".strip()


def send_email(alert: AlertInfo, report: TriageReport):
    subject = f"[KubeTriage] {report.category} — {alert.namespace}/{alert.pod}"
    body = _format_email_body(alert, report)

    msg = MIMEMultipart()
    msg["From"] = settings.smtp_user
    msg["To"] = settings.notify_to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, settings.notify_to, msg.as_string())
        logger.info(f"========== Email sent to {settings.notify_to} for {alert.pod} ===========")
    except Exception as e:
        logger.error(f"========== Failed to send email for {alert.pod}: {e} ==========")