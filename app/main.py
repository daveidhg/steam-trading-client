from dotenv import load_dotenv
import os
from services import steam_client

load_dotenv()

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_ID = os.getenv("STEAM_ID")
STEAM_GUARD = os.getenv("STEAM_GUARD")
STEAM_USERNAME = os.getenv("STEAM_USERNAME")
STEAM_PASSWORD = os.getenv("STEAM_PASSWORD")

def main():
    print('Main started')
    client = steam_client.SteamClientService(STEAM_API_KEY, STEAM_USERNAME, STEAM_PASSWORD, STEAM_GUARD)

    client.testing()

    assetId = input("Asset id: ")

    client.send_trade_offer("https://steamcommunity.com/tradeoffer/new/?partner=249336381&token=c3WESCur", assetId)


if __name__ == "__main__":
    main()