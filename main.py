from config import env_is_ok
from mailbox_client import mailbox
from image_processing import extract_numbers
from mail import send_mail
from dotenv import load_dotenv
import os
import logging
import datetime as dt


def main():

    load_dotenv()

    logging.basicConfig(filename=os.environ.get(
        'LOGFILE_PATH') or 'task.txt', level=logging.INFO)
    if env_is_ok():
        logging.info(f'[{dt.datetime.now()}] Processing task started.')
        mailbox()
        numbers = extract_numbers()
        send_mail(numbers)
        logging.info(f'[{dt.datetime.now()}] Processing task finished.')
    else:
        logging.critical(
            f'[{dt.datetime.now()}] .env file not configured properly.')
        raise ValueError(
            '.env file must contain valid MAIL_SERVER, MAIL_ACCOUNT, MAIL_PASSWORD, RECEIVER_MAIL and OUTPUT_DIR variables.')


if __name__ == '__main__':
    main()
