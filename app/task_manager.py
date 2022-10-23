from flask import request
from . import app
from .access import access
import json
from .database import sql, db
from .modules import get_timestamp, tasks_formatter,TASKS_PARAMS

@app.route('/get-active-drivers/<login>/<token>',  endpoint='get_active_drivers')
@access([2,3])
def get_active_drivers(login, token):

    in_time = request.args.get('in_time')
    long = request.args.get('long')
    in_time = int(in_time if in_time and in_time.isdigit() else 0)
    long = int(long if long and long.isdigit() else 25)
    if in_time:
        q = f"""
        SELECT DISTINCT us.id, us.login, us.name, b.number, m.count_seats, m.type
    FROM tasks as t, (SELECT u.id, login, last_name || ' ' || first_name || ' ' || father_name as name, u.bus_id FROM users as u WHERE bus_id > 0
EXCEPT
SELECT u.id, login, last_name || ' ' || first_name || ' ' || father_name as name, u.bus_id FROM users as u, tasks as t WHERE timestamp_task BETWEEN {in_time} AND {in_time+long*60*1000}) as us
    INNER JOIN buses as b ON us.bus_id = b.number INNER JOIN bus_models as m ON m.id=b.model WHERE us.bus_id > 0  AND ARRAY[us.id] <@ users AND status != 'active'
"""
    else:
        q = f"""SELECT u.id, login, last_name || ' ' || first_name || ' ' || father_name, b.number, m.count_seats, m.type 
    FROM users as u
    INNER JOIN buses as b ON u.bus_id = b.number INNER JOIN bus_models as m ON m.id=b.model WHERE bus_id > 0"""

    sql.execute(q)
    rows = sql.fetchall()
    users = []
    for row in rows:
        users.append({
        'id':row[0],
        'login':row[1],
        'name':row[2],
        'bus_info':{
            'number':row[3],
            'count_seats':row[4],
            'type':row[5]
        }
    })
    return json.dumps({'active_users': users}, ensure_ascii=False), 200


@app.route('/get-task/<login>/<token>', endpoint='get_task')
@access([1,2,3])
def get_task(login, token):
    id = request.args.get('id','')
    if not id or not id.isdigit():
        return json.dumps({'message': 'Вы не указали ID задачи!'}, ensure_ascii=False), 500

    sql.execute(f"SELECT {','.join(TASKS_PARAMS)} FROM tasks WHERE id = {id}")
    row = sql.fetchone()
    if not row:
        return json.dumps({'message': 'Задача с таким ID не найдена!'}, ensure_ascii=False), 500

    return json.dumps(tasks_formatter([row])[0], ensure_ascii=False), 200


@app.route('/edit-task/<login>/<token>', methods=('POST',"GET"), endpoint='edit_task')
@access([1,2,3])
def edit_task(login, token):
    if request.method != 'POST':
        return {"message": 'invalid message'}, 500

    body = request.json

    if not body:
        return json.dumps({'message': 'Тело запроса пустое, не надо так!'}, ensure_ascii=False), 500

    id = body.get('id')

    if not id or not isinstance(id, int):
        return json.dumps({'message': 'ID задачи не указано, не надо так!'}, ensure_ascii=False), 500

    q = ''
    del body['id']
    # request.
    timestamp_task = body.get('timestamp_task')
    process_time = body.get('process_time')

    sql.execute(f"""
        UPDATE tasks SET users = ARRAY[(SELECT u.id FROM users as u, tasks as t WHERE ARRAY[u.id] <@ t.users EXCEPT SELECT DISTINCT u.id FROM users as u, 
        (SELECT users FROM tasks WHERE {timestamp_task} BETWEEN timestamp_task AND timestamp_task+{process_time}*60000) as us
        WHERE ARRAY[u.id] <@ users)] WHERE id = {id}""")
    sql.execute("UPDATE tasks SET users = '{}' WHERE users = '{NULL}'")
    is_update_drivers = sql.rowcount
    db.commit()
    for key, val in body.items():
        if type(val) == str:
            q+=f"{key}='{val}', "
        elif type(val) == list:
            q+=f"{key}=ARRAY{val}, "
        elif type(val) == int:
            q += f"{key}={val}, "
    sql.execute(f"""UPDATE tasks SET {q[:-2]} WHERE id={id}""")
    db.commit()
    return json.dumps({'message': f'Данные успешно обновлены! {"Но было изменено колличество автобусов!!! " if is_update_drivers > 0 else ""}'}, ensure_ascii=False), 500


@app.route('/add-task/<login>/<token>', methods=('POST',"GET"), endpoint='add_task')
@access([2,3])
def add_task(login, token):
    if request.method != 'POST':
        return {"message":'invalid message'}, 500

    body = request.json

    if not body:
        return json.dumps({'message': 'Тело запроса пустое, не надо так!'}, ensure_ascii=False), 500

    users = body.get('users',[])
    timestamp_task = body.get('timestamp_task',get_timestamp())
    description = body.get('description','Диспетчер не оставил сообщение!')
    timestamp_update = timestamp_init = get_timestamp()
    target_point_id = body.get('target_point_id',-1)
    source_point_id = body.get('source_point_id',-1)
    count_passengers = body.get('count_passengers',0)
    process_time = body.get('process_time',25)

    if count_passengers < 1:
        return json.dumps({'message': 'Введите колличество пассажиров!'}, ensure_ascii=False), 500

    status = 'new'

    sql.execute(f"""INSERT INTO tasks (users, timestamp_task, description, timestamp_init, timestamp_update, status,target_point_id, source_point_id, process_time, count_passengers) 
                                VALUES ({"array" + str(users) if users else "'{}'"}, {timestamp_task},'{description}',{timestamp_update},{timestamp_init},'{status}',{target_point_id},{source_point_id},{process_time}, {count_passengers})""")
    db.commit()

    return json.dumps({'users':users, 'timestamp_task':timestamp_task, 'description':description,
                       'timestamp_update':timestamp_update, 'timestamp_init':timestamp_init,'target_point_id':target_point_id,'source_point_id':source_point_id, 'process_time':process_time, 'count_passengers':count_passengers}, ensure_ascii=False), 200

@app.route('/get-tasks/<login>/<token>', endpoint='get_tasks')
@access([1,2,3])
def get_tasks(login, token):
    if request.method != 'GET':
        return json.dumps({'message': 'Invalid method'}, ensure_ascii=False), 500


    page = request.args.get('page')
    page = int(page) if page and page.isdigit() and int(page) > 0 else 0

    limit = request.args.get('limit')
    limit = int(limit) if limit and limit.isdigit() and int(limit) > 0 else 25

    sql.execute(f"""SELECT {', '.join(TASKS_PARAMS)} FROM tasks ORDER BY timestamp_task DESC OFFSET {limit*page} LIMIT {limit}""")
    rows = sql.fetchall()
    tasks = tasks_formatter(rows)

    return json.dumps({'tasks': tasks}, ensure_ascii=False), 200



