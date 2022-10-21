import json
import smtplib
import flask
import config
from flask_socketio import SocketIO
from flask import request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import create_conn
from random import choices
from threading import Thread
from hashlib import sha256
from access import access
app = flask.Flask('AIRPORT')

app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD
app.config['SECRET_KEY'] = config.SECRET_KEY


sql, db = create_conn()

def mail_send(target: str, msg: MIMEMultipart):
    mail = smtplib.SMTP_SSL('smtp.yandex.ru', 465)
    mail.login(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
    msg['From'] = app.config["MAIL_USERNAME"]

    mail.sendmail(app.config['MAIL_USERNAME'], target, msg.as_string())
    mail.quit()


def genCode(lenCode:int = 8):
    return ''.join(choices('1234567890qwertyuiopasdfgjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM', k=lenCode))


@app.route('/add-new-acc/<login>/<token>',methods=('POST','GET'), endpoint='account_handler')
@access([3])
def account_handler(login, token):
    if request.method == 'GET':
        sql.execute('SELECT id, title FROM roles')
        roles_list = sql.fetchall()
        return json.dumps({'roles': roles_list}, nsure_ascii=False), 200
    elif request.method != 'POST':
        return {'message':'Invalid method'},500

    body = request.json

    login = body.get("login").lower()
    email = body.get("email").lower()
    sql.execute(f"""SELECT COUNT(*) FROM users WHERE login='{body.get("login")}' OR email='{body.get("email")}'""")
    row = sql.fetchone()
    if row[0] > 0:
        return json.dumps({'message': 'Пользователь под этим логином или почтой уже существует'},
                          ensure_ascii=False), 500
    password = genCode()
    pswd = sha256(password.encode('utf-8')).hexdigest()
    token = sha256(f'{pswd}-{login}-{email}'.encode('utf-8')).hexdigest()
    sql.execute(
        f"""INSERT INTO users (login, email, password,token, first_name, last_name, father_name, role_id) VALUES ('{login}','{email}','{pswd}','{token}','{body.get("first_name")}','{body.get("last_name")}','{body.get("father_name")}',{body.get("role_id")})""")
    db.commit()
    msg = MIMEMultipart()
    msg['Subject'] = 'Код подтверждения!'
    html = f'<html><head></head><body><h1 style="text-align:center">Данные для входа:</h1><h4 style="text-align:center">Логин: {body.get("login")}</h4><h2>Пароль: {password}</h2></body></html>'
    body_mail = MIMEText(html, 'html')
    msg.attach(body_mail)
    Thread(target=mail_send, args=(body.get('email'), msg)).start()
    return json.dumps({'message': 'Письмо с данными для входа отправлены на почту сотрудника!'},ensure_ascii=False), 200


@app.route('/login', methods=('POST','GET'))
def login_handler():

    if request.method == 'POST':
        body = request.json

        login = body.get('login')
        password = sha256(body.get('password').encode('utf-8')).hexdigest()
        sql.execute(f"""SELECT token FROM users WHERE login='{login}' AND password='{password}'""")
        row = sql.fetchone()
        if len(row) < 1:
            return json.dumps({'message':'Аккаунт с таким логином не найден или неверный пароль!'}, ensure_ascii=False), 500
        return json.dumps({'login':login, 'token':row[0]}, nsure_ascii=False), 200



socketio = SocketIO(app,engineio_logger=False,logger=False)
socketio.init_app(app, cors_allowed_origins="*")
socketio.run(app, debug=config.debug, host="0.0.0.0", port=82)  # 0.0.0.0


