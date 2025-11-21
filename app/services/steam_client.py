from steampy.client import SteamClient
from steampy.models import Asset, GameOptions

class SteamClientService:
    def __init__(self, api_key, username, password, steam_guard):
        self.client = SteamClient(api_key, username, password, steam_guard)
        self.client.login()


    def send_trade_offer(self, trade_url, asset_id, message = ''):
        item = [Asset(asset_id, GameOptions.CS)]

        offer = self.client.make_offer_with_url(
            item,
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

