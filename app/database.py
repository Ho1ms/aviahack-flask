import psycopg2
from .config import data_connect

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
sql.execute("""INSERT INTO roles (id,title) VALUES (1,'Водитель'),(2,'Диспетчер'),(3,'Руководитель') ON CONFLICT DO NOTHING""")

sql.execute("""
CREATE TABLE IF NOT EXISTS bus_models (
    id SERIAL PRIMARY KEY,
    type INT,
    count_seats INT
)
""")
sql.execute(f"""INSERT INTO bus_models (id, type, count_seats) VALUES (1, 30,100),(2,10,50) ON CONFLICT DO NOTHING""")
sql.execute("""
    CREATE TABLE IF NOT EXISTS buses (
        number INTEGER PRIMARY KEY,
        model INT,
        FOREIGN KEY (model) REFERENCES bus_models(id)
    )
""")
sql.execute(f"""INSERT INTO buses (number, model) VALUES (0, 1),(666,1),(777,2),(123,2)  ON CONFLICT DO NOTHING""")
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
    role_id INT DEFAULT 1,
    bus_id INT DEFAULT 0,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (bus_id) REFERENCES buses(number)
    )
    """
)

sql.execute(f"""
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    users INT[],
    timestamp_task BIGINT,
    process_time INT,
    count_passengers INT,
    description VARCHAR(1024),
    timestamp_init BIGINT,
    timestamp_update BIGINT,
    status VARCHAR(32),
    target_point_id INT,
    source_point_id INT
    
)
""")
sql.execute(f"""INSERT INTO users (id, login, email, password,token, first_name, last_name, father_name, role_id) VALUES (1,'holms','danila@ginda.info','5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8','super_puper_token_hash','Данила','Гинда','Александрович',3) ON CONFLICT DO NOTHING """)
db.commit()
db.close()