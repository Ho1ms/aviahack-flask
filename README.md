Комадна запуска:

pip install -r requirements.txt
python3 run.py

Ещё нужен конфиг в env:
MAIL_USERNAME = "имя почты для рассылки"
MAIL_PASSWORD = "пароль от неё"
SECRET_KEY = "ключ шифрования"
data_connect = {'dbname':'hackaton','user':'postgres','host':'localhost','password':'пароль'} 
