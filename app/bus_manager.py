from flask import request
from . import app
from .access import access
import json
from .database import create_conn
sql, db = create_conn()

@app.route('/get-free-bus/<login>/<token>',endpoint='get_free_bus')
@access([1,2,3])
def get_free_bus(login,token):
    params = ('number', 'model', 'type', 'count_seats')
    sql.execute(f'SELECT {", ".join(params)} FROM buses as b INNER JOIN bus_models as bm ON b.model = bm.id LEFT JOIN users as u ON b.number > 0 AND b.number = u.bus_id WHERE u.id is NULL AND b.number > 0 ')
    rows = sql.fetchall()
    data = []
    for row in rows:
        bus = {}
        for i, key in enumerate(params):
            bus[key] = row[i]
        data.append(bus)
    return json.dumps({'free_buses':data}, ensure_ascii=False), 200

@app.route('/bus-getter/<login>/<token>', methods=("POST","GET"), endpoint='bus_getter')
@access([1,2,3])
def bus_getter(login, token):
    if request.method != 'POST':
        return {"message": 'invalid message'}, 500

    body = request.json

    if not body:
        return json.dumps({'message': 'Тело запроса пустое, не надо так!'}, ensure_ascii=False), 500

    bus_number = body.get('bus_number')
    if body.get('type') == 'start':
        sql.execute(f"SELECT COUNT(*) FROM users WHERE bus_id = {bus_number}")
        isNotFree = sql.fetchone()[0]
        if isNotFree:
            return json.dumps({'message': 'Этот автобус занят!'}, ensure_ascii=False), 500

        try:
            sql.execute(f"UPDATE users SET bus_id = {bus_number} WHERE login='{login}' AND token='{token}'")
        except:
            return json.dumps({'message': 'Этот автобус не найден в базе!'}, ensure_ascii=False), 500
        return json.dumps({'message': f'Вы успешно взяли себе автобус №{bus_number}'}, ensure_ascii=False), 200
    elif body.get('type') == 'end':
        sql.execute(f"SELECT COUNT(*) FROM users WHERE bus_id = {bus_number} AND login='{login}' AND token='{token}'")
        isFree = sql.fetchone()[0]

        if not isFree:
            return json.dumps({'message': 'Это не ваш автобус!'}, ensure_ascii=False), 500

        try:
            sql.execute(f"UPDATE users SET bus_id = 0 WHERE login='{login}' AND token='{token}'")
        except:
            return json.dumps({'message': 'Этот автобус не найден в базе!'}, ensure_ascii=False), 500
        return json.dumps({'message': f'Вы успешно закончили смену на автобусе №{bus_number}'}, ensure_ascii=False), 200


