from dotenv import load_dotenv
import os

load_dotenv()


def env_is_ok():
    """
    Check required environment varibles are set in .env file. Return True if .env file is ok. False otherwise
    """
    if os.environ.get('MAIL_SERVER') and os.environ.get('MAIL_ACCOUNT') and os.environ.get('MAIL_PASSWORD') and os.environ.get('OUTPUT_DIR') and os.environ.get('RECEIVER_MAIL'):
        return True
    else:
        return False
