import psycopg2
from config import data_connect

def create_conn():
    db = psycopg2.connect(**data_connect)
    sql = db.cursor()
    return sql, db

sql, db = create_conn()

sql.execute(
    """
     CREATE TABLE IF NOT EXISTS roles (
     id SERIAL PRIMARY KEY,
     title VARCHAR(128)
     )
    """
)
sql.execute("""INSERT INTO roles (title) VALUES ('Водитель'),('Диспетчер'),('Руководитель')""")

sql.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    login VARCHAR(64),
    email VARCHAR(128),
    password VARCHAR(64),
    token varchar(64),
    first_name VARCHAR(128),
    last_name VARCHAR(128),
    father_name VARCHAR(128),
    role_id int,
    FOREIGN KEY (role_id) REFERENCES roles(id)
    )
    """
)

db.commit()
db.close()