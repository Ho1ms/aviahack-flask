import json
from .database import create_conn
from flask_cors import cross_origin

def access(access_roles:list ):

    def func_inner(func):
        @cross_origin()
        def inner(**kwargs):
            login = kwargs.get('login')
            token = kwargs.get('token')

            sql, db = create_conn()

            sql.execute(f"""SELECT role_id FROM users WHERE login='{login}' AND token = '{token}'""")
            row = sql.fetchone()

            db.close()

            if not row:
                return json.dumps({'message': 'Вы не авторизованы!'},ensure_ascii=False), 500
            elif row[0] not in access_roles:
                return json.dumps({'message': 'У вас нет доступа к этой странице!'},ensure_ascii=False), 500

            return func(**kwargs)

        return inner
    return func_inner