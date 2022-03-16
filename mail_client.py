import email
import os
from dotenv import load_dotenv
import imaplib

load_dotenv()

def connect():
    """
    Create SSL connection to mailbox. Return a IMA4_SSL object.
    """
    if not os.environ.get('MAIL_SERVER') == None or not os.environ.get('MAIL_ACCOUNT') == None or not os.environ.get('MAIL_PASSWORD') == None:
        conn = imaplib.IMAP4_SSL(os.environ.get('MAIL_SERVER')) 
        conn.login(user=os.environ.get('MAIL_ACCOUNT'),
                    password=os.environ.get('MAIL_PASSWORD'))
        conn.select(readonly=False)

        return conn
    else:
        raise ValueError('.env file must contain valid MAIL_SERVER, MAIL_ACCOUNT and MAIL_PASSWORD variables.')

def download_all_attachments(conn: imaplib.IMAP4_SSL, email_id: bytes):
    """
    Download all files attached in message.
    """
    typ, data = conn.fetch(email_id, '(RFC822)')
    email_body = data[0][1]
    mail = email.message_from_bytes(email_body)
    if mail.get_content_maintype() != 'multipart':
        return
    for part in mail.walk():
        if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
            open(os.environ.get('OUTPUT_DIR') + '\\' + part.get_filename(), 'wb').write(part.get_payload(decode=True))

def mailbox():
    """
    Stablish a connection with mailbox, search all messages with defined subject and download all files attached to message.
    """
    conn = connect()

    typ, data = conn.search(None, '(SUBJECT "Imagen-Procesar")')
    emails_id = data[0].split()
    
    for _id in emails_id:
        download_all_attachments(conn, _id)

    conn.close()
    conn.logout()