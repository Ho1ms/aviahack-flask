import datetime
from random import choices
import smtplib
from email.mime.multipart import MIMEMultipart
from . import app
def mail_send(target: str, msg: MIMEMultipart):
    mail = smtplib.SMTP_SSL('smtp.yandex.ru', 465)
    mail.login(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
    msg['From'] = app.config["MAIL_USERNAME"]

    mail.sendmail(app.config['MAIL_USERNAME'], target, msg.as_string())
    mail.quit()


def genCode(lenCode:int = 8):
    return ''.join(choices('1234567890qwertyuiopasdfgjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM', k=lenCode))



def get_timestamp(date=None) -> int:
    date = date or datetime.datetime.now()
    return int(''.join(str(date.timestamp()).split('.'))[0:13].ljust(13,'0'))

TASKS_PARAMS = ['id', 'users', 'timestamp_task', 'description', 'timestamp_init', 'timestamp_update', 'status','process_time','count_passengers','target_point_id', 'source_point_id']
def tasks_formatter(tasks_array:list) -> list:

    tasks = []
    for row in tasks_array:
        task = {}
        for i, param in enumerate(TASKS_PARAMS):
            task[param] = row[i]
        tasks.append(task)
    return tasks

