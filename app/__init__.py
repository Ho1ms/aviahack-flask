from flask import Flask
from os import urandom, path, getcwd
from .config import *
from flask_socketio import SocketIO
from flask_cors import CORS, cross_origin

import logging
log = logging.getLogger('werkzeug')
log.disabled = True

def dir(folder:str)->str:
    return path.join(getcwd(), 'app', folder)

app = Flask('AIRPORT')

app.logger.disabled = True
app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD
app.config['SECRET_KEY'] = config.SECRET_KEY
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


socketio = SocketIO(app,engineio_logger=False,logger=False)
socketio.init_app(app, cors_allowed_origins="*")

from . import auth_manager, task_manager, app


