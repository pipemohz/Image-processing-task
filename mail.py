import logging
import datetime as dt
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


def send_mail(data: list):
    """
    Send email to RECEIVER_MAIL list with input data.
    """

    message = MIMEMultipart()
    message['From'] = os.environ.get('MAIL_ACCOUNT')
    message['To'] = os.environ.get('RECEIVER_MAIL')
    message['Subject'] = 'Tarea de procesamiento de imagen completada.'

    mail_content = f"La imagen requerida fue procesada. El valor detectado fue {data[0]}"
    message.attach(MIMEText(mail_content, 'plain'))

    with smtplib.SMTP(host=os.environ.get('MAIL_SERVER'), port=587) as conn:
        conn.starttls()
        conn.login(user=os.environ.get('MAIL_ACCOUNT'),
                   password=os.environ.get('MAIL_PASSWORD'))

        conn.sendmail(from_addr=os.environ.get('MAIL_ACCOUNT'), to_addrs=os.environ.get(
            'RECEIVER_MAIL').split(','), msg=message.as_string())

    logging.info(
        f'[{dt.datetime.now()}] Notification email sent successfully.')
