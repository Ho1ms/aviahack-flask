#! C:/Users/ghind/AppData/Local/Programs/Python/Python39/python.exe

from app import socketio, app, config

if __name__ == '__main__':

    print('Starting...')
    socketio.run(app, debug=config.debug,host="0.0.0.0", port=80) # 0.0.0.0
