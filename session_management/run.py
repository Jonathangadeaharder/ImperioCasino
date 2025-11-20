from .imperioApp import app, socketio
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    logging.info("Starting the app with SocketIO support on port 5011")
    # Use socketio.run() instead of app.run() for WebSocket support
    socketio.run(app, host='0.0.0.0', port=5011, debug=True)
