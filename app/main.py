from dotenv import load_dotenv
import os
from flask import Flask
from services.steam_client import SteamClientService
from controllers.v1.trade_controller import TradeController
import logging

load_dotenv()

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_ID = os.getenv("STEAM_ID")
STEAM_GUARD = os.getenv("STEAM_GUARD")
STEAM_USERNAME = os.getenv("STEAM_USERNAME")
STEAM_PASSWORD = os.getenv("STEAM_PASSWORD")
STEAM_KEEPALIVE_SECONDS = int(os.getenv("STEAM_KEEPALIVE_SECONDS", "300"))

def create_app():
    app = Flask(__name__)

    client = SteamClientService(
        STEAM_API_KEY,
        STEAM_USERNAME,
        STEAM_PASSWORD,
        STEAM_GUARD,
        keepalive_interval=STEAM_KEEPALIVE_SECONDS,
    )

    trade_controller = TradeController(client)

    app.register_blueprint(trade_controller.blueprint, url_prefix="/trades")

    return app


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("app.log")
        ]
    )
    
    logging.info('Main started')
    app = create_app()

    app.run(
        host='127.0.0.1',
        port=8080,
        debug=True,
        use_reloader=False,
        threaded=False
    )


if __name__ == "__main__":
    main()