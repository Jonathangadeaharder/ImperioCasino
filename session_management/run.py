from .imperioApp import app
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    logging.info("Starting the app on port 5011")
    app.run()
