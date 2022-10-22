import json
import os
import flask
from .config import *
from flask import request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread
from hashlib import sha256
from . import app
from .access import access
from .database import create_conn
from flask_cors import cross_origin
from .modules import genCode, mail_send, tasks_formatter,TASKS_PARAMS

sql, db = create_conn()


@app.route('/add-new-acc/<login>/<token>',methods=('POST','GET'), endpoint='account_handler')
@access([3])
def account_handler(login, token):
    if request.method == 'GET':
        sql.execute('SELECT id, title FROM roles')
        roles_list = sql.fetchall()
        return json.dumps({'roles': roles_list}, ensure_ascii=False), 200
    elif request.method != 'POST':
        return {'message':'Invalid method'},500

    body = request.json

    login = body.get("login",'').lower()
    email = body.get("email",'').lower()
    sql.execute(f"""SELECT COUNT(*) FROM users WHERE login='{body.get("login")}' OR email='{body.get("email")}'""")
    row = sql.fetchone()
    if row[0] > 0:
        return json.dumps({'message': 'Пользователь под этим логином или почтой уже существует'},
                          ensure_ascii=False), 500
    password = genCode()
    pswd = sha256(password.encode('utf-8')).hexdigest()
    token = sha256(f'{pswd}-{login}-{email}'.encode('utf-8')).hexdigest()
    sql.execute( f"""INSERT INTO users (login, email, password,token, first_name, last_name, father_name, role_id) VALUES ('{login}','{email}','{pswd}','{token}','{body.get("first_name")}','{body.get("last_name")}','{body.get("father_name")}',{body.get("role_id")})""")
    db.commit()
    msg = MIMEMultipart()
    msg['Subject'] = 'Данные для входа!'
    html = f'<html><head></head><body><h1 style="text-align:center">Данные для входа:</h1><h4 style="text-align:center">Логин: {body.get("login")}</h4><h3 style="text-align:center">Пароль: {password}</h3></body></html>'
    body_mail = MIMEText(html, 'html')
    msg.attach(body_mail)
    Thread(target=mail_send, args=(body.get('email'), msg)).start()
    return json.dumps({'message': 'Письмо с данными для входа отправлено на почту сотрудника!'},ensure_ascii=False), 200

@app.route('/ping')
def ping():
    return {'message':'pong'}, 200

@app.route('/login', methods=('POST','GET'))
@cross_origin()
def login_handler():

    if request.method == 'POST':
        body = request.json
        if not body:
            return json.dumps({'message':'Тело запроса пустое, не надо так!'}, ensure_ascii=False), 500
        login = body.get('login')
        password = sha256(body.get('password','').encode('utf-8')).hexdigest()
        sql.execute(f"""SELECT token FROM users WHERE login='{login}' AND password='{password}'""")
        row = sql.fetchone()
        if not row:
            return json.dumps({'message':'Аккаунт с таким логином не найден или неверный пароль!'}, ensure_ascii=False), 500
        return json.dumps({'login':login, 'token':row[0]}, ensure_ascii=False), 200
    return json.dumps({'message':'Требуется POST запрос!'}, ensure_ascii=False), 500


@app.route('/auth/me/<login>/<token>', endpoint='authMe')
@access([1,2,3])
def auhtMe(login, token):
    sql.execute(f"""SELECT u.id, login, email, last_name || ' ' || first_name || ' ' || father_name, bus_id, count_seats,type FROM users as u INNER JOIN buses as b ON u.bus_id = b.number INNER JOIN bus_models as m ON m.id=b.model WHERE token='{token}' AND login='{login}'""")
    row = sql.fetchone()

    if not row:
        return json.dumps({'message': 'Аккаунт не найден!'}, ensure_ascii=False), 500

    user_info = {
        'id':row[0],
        'login':row[1],
        'email':row[2],
        'name':row[3],
        'bus_info':{
            'number':row[4],
            'count_seats':row[5],
            'type':row[6]
        }

    }

    page = request.args.get('page')
    page = int(page) if page and page.isdigit() and int(page) > 0 else 0

    limit = request.args.get('limit')
    limit = int(limit) if limit and limit.isdigit() and int(limit) > 0 else 25

    sql.execute(f"""SELECT {', '.join(TASKS_PARAMS)} FROM tasks WHERE status in ('active','new') AND ARRAY[{user_info['id']}] <@ users ORDER BY timestamp_task DESC OFFSET {limit*page} LIMIT {limit}""")
    rows = sql.fetchall()
    tasks = tasks_formatter(rows)

    return json.dumps({'user':user_info, 'tasks':tasks}, ensure_ascii=False), 200


