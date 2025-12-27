from steampy.client import SteamClient
from steampy.models import Asset, GameOptions
from steampy.exceptions import InvalidCredentials
from steampy import guard
from requests import Session, cookies as cookie_utils
import json
import os
import logging

SESSION_PATH = "app/storage/session.json"

class SteamClientService:
    def __init__(self, api_key, username, password, steam_guard):
        self.api_key = api_key
        self.username = username
        self.password = password
        self.steam_guard = steam_guard

        self.client = None

        if self._load_session():
            logging.info("Restored Steam session from cookies.")
            if self._validate_session():
                logging.info("Session is valid.")
                return
            else:
                logging.info("Saved session invalid. Performing full login...")

        logging.info("Logging in with username + Steam Guard…")
        self._login_fresh()

    def _login_fresh(self):
        self.client = SteamClient(self.api_key)
        try:
            self.client.login(self.username, self.password, self.steam_guard)
        except InvalidCredentials:
            raise Exception("Steam login failed — invalid SteamGuard or credentials.")

        self._save_session()
        logging.info("Saved fresh login cookies.")

    def _load_session(self):
        if not os.path.exists(SESSION_PATH):
            return False

        try:
            with open(SESSION_PATH, "r") as f:
                data = json.load(f)
        except Exception:
            return False

        cookies = data.get("cookies")
        if not cookies:
            return False

        self.client = SteamClient(self.api_key)
        self.client.steam_guard = guard.load_steam_guard(self.steam_guard)

        jar = cookie_utils.RequestsCookieJar()
        for c in cookies:
            cookie = cookie_utils.create_cookie(
                name=c.get("name"),
                value=c.get("value"),
                domain=c.get("domain"),
                path=c.get("path", "/"),
                expires=c.get("expires"),
                secure=c.get("secure", False),
                rest=c.get("rest", None),
            )
            jar.set_cookie(cookie)
        self.client._session.cookies = jar

        # Mark the client as having a restored login so steampy will treat it authenticated
        self.client.was_login_executed = True

        return True

    def _validate_session(self):
        try:
            # Authenticated endpoint
            self.client.get_my_inventory(GameOptions.CS)
            return True
        except Exception:
            return False


    def _save_session(self):
        cookies = []
        for c in self.client._session.cookies:
            cookies.append({
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path,
                "expires": c.expires,
                "secure": c.secure,
                "rest": c._rest,
            })
        
        folder = os.path.dirname(SESSION_PATH)
        os.makedirs(folder, exist_ok=True)

        with open(SESSION_PATH, "w") as f:
            json.dump({"cookies": cookies}, f)


    def send_trade_offer(self, trade_url, asset_ids, message = ''):
        items = [Asset(asset_id, GameOptions.CS) for asset_id in asset_ids]

        offer = self.client.make_offer_with_url(
            items,
            [],
            trade_url,
            message
        )

        return offer.get("tradeofferid")

    def cancel_trade_offer(self, offer_id):
        self.client.cancel_trade_offer(offer_id)
        return True

    def get_offer_status(self, offer_id):
        offers = self.client.get_trade_offers()
        return offers.get(offer_id, "unknown")
    
    def get_cs_inventory(self):
        return self.client.get_my_inventory(GameOptions.CS)
