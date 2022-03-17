# Image-processing-task

Project for automatic image processing of images downloaded from a mailbox (MAIL_ACCOUNT). A number is extracted from each image downloaded and send by email to a list 
of receivers (RECEIVER_MAIL)

## Installation 🔧

Clone the repository in a your work folder.

## Configuration

### Download all packages required

pip install -r requirements.txt

### Create an environment file

You can create a .env file for project configuration. It must contain following variables:

* MAIL_SERVER='imap_mail_servername'
* MAIL_ACCOUNT='mail_account_sender'
* MAIL_PASSWORD='mail_account_sender_password'
* RECEIVER_MAIL='receiver1.example.com,receiver2.example.com'
* OUTPUT_DIR='path_to_download_images'

Optional

* LOGFILE_PATH='path_to_log'

