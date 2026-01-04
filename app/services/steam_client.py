from steampy.client import SteamClient
from steampy.models import Asset, GameOptions
from steampy.exceptions import InvalidCredentials
from steampy import guard
from requests import cookies as cookie_utils
from functools import wraps
import json
import os
import logging
import threading
import time

SESSION_PATH = "app/storage/session.json"

class SteamClientService:
    def __init__(self, api_key, username, password, steam_guard, keepalive_interval=300):
        self.api_key = api_key
        self.username = username
        self.password = password
        self.steam_guard = steam_guard
        self._keepalive_interval = max(60, int(keepalive_interval))
        self._last_session_check = 0.0
        self._keepalive_stop_event = threading.Event()
        self._keepalive_thread = None

        self.client = None

        session_restored = self._load_session()
        if session_restored:
            logging.info("Restored Steam session from cookies.")
            if not self._validate_session():
                logging.info("Saved session invalid. Performing full login...")
                self._login_fresh()
            else:
                logging.info("Session is valid.")
        else:
            logging.info("Logging in with username + Steam Guard...")
            self._login_fresh()

        self._last_session_check = time.time()
        self._start_keepalive_thread()

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

        self.client._access_token = self.client._set_access_token()

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

    def _ensure_session(self, force=False):
        now = time.time()
        if not force and (now - self._last_session_check) < self._keepalive_interval:
            return

        logging.debug("Performing Steam session keep-alive (force=%s)", force)
        try:
            if self.client.is_session_alive():
                self._last_session_check = time.time()
                return
        except Exception as exc:
            logging.warning(f"Steam keep-alive ping failed: {exc}")

        logging.info("Steam session expired or unreachable. Re-authenticating...")
        self._login_fresh()
        self._last_session_check = time.time()

    def _start_keepalive_thread(self):
        if self._keepalive_thread and self._keepalive_thread.is_alive():
            return

        self._keepalive_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
        self._keepalive_thread.start()

    def _keepalive_loop(self):
        while not self._keepalive_stop_event.wait(self._keepalive_interval):
            try:
                self._ensure_session(force=True)
            except Exception as exc:
                logging.warning(f"Background keep-alive failed: {exc}")

    def retry_failed_request(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            self._ensure_session()
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                logging.warning(f"Steam request failed, retrying after session refresh: {e}")
                self._ensure_session(force=True)
                return func(self, *args, **kwargs)

        return wrapper


    @retry_failed_request
    def send_trade_offer(self, trade_url, asset_ids, message = ''):
        items = [Asset(asset_id, GameOptions.CS) for asset_id in asset_ids]

        offer = self.client.make_offer_with_url(
            items,
            [],
            trade_url,
            message
        )

        print(offer)

        return offer.get("tradeofferid")

    @retry_failed_request
    def cancel_trade_offer(self, offer_id):
        self.client.cancel_trade_offer(offer_id)
        return True

    @retry_failed_request
    def get_trade_offer(self, offer_id):
        return self.client.get_trade_offer(offer_id, use_webtoken=True)
    
    @retry_failed_request
    def get_cs_inventory(self):
        return self.client.get_my_inventory(GameOptions.CS)
