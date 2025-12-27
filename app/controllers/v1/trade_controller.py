from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest, InternalServerError
from services.steam_client import SteamClientService
import logging


class TradeController:
    def __init__(self, steam_client_service: SteamClientService):
        self.steam_client_service = steam_client_service
        self.blueprint = Blueprint("trade", __name__)

        self.blueprint.add_url_rule(
            "/create",
            view_func=self.create_offer,
            methods=["POST"]
        )
        self.blueprint.add_url_rule(
            "/<offer_id>/cancel",
            view_func=self.cancel_offer,
            methods=["POST"]
        )
        self.blueprint.add_url_rule(
            "/<offer_id>/status",
            view_func=self.offer_status,
            methods=["GET"]
        )
        self.blueprint.add_url_rule(
            "/inventory",
            view_func=self.get_cs_inventory,
            methods=["GET"]
        )

    def get_cs_inventory(self):
        """
        Get cs inventory including asset Ids 
        """
        try:
            inventory = self.steam_client_service.get_cs_inventory()

            return jsonify({
                "success": True,
                "inventory": inventory
            }), 200
        
        except Exception as e:
            logging.error(f"Failed to get cs inventory: {e}")
            raise InternalServerError("Failed to get cs inventory")


    def create_offer(self):
        """
        Create a new trade offer to a partner Steam user.
        """
        data = request.get_json()

        if not data:
            raise BadRequest("Missing JSON body.")

        required_fields = ["partner_trade_url", "asset_ids"]
        for field in required_fields:
            if field not in data:
                raise BadRequest(f"Missing required field: {field}")

        try:
            offer_id = self.steam_client_service.send_trade_offer(
                trade_url=data["partner_trade_url"],
                asset_ids=data["asset_ids"]
            )

            return jsonify({
                "success": True,
                "offer_id": offer_id
            }), 200

        except Exception as e:
            logging.error(f"Failed to create trade offer: {e}")
            raise InternalServerError("Failed to create trade offer.")

    def cancel_offer(self, offer_id):
        """
        Cancel an existing trade offer.
        """

        try:
            success = self.steam_client_service.cancel_trade_offer(
                offer_id
            )

            return jsonify({
                "success": success,
                "offer_id": offer_id
            }), 200

        except Exception as e:
            logging.error(f"Failed to cancel trade offer: {e}")
            raise InternalServerError("Failed to cancel trade offer.")

    def offer_status(self, offer_id):
        """
        Get status of an existing trade offer.
        """
        try:
            status = self.steam_client_service.get_offer_status(offer_id)

            return jsonify({
                "success": True,
                "offer_id": offer_id,
                "status": status
            }), 200

        except Exception as e:
            logging.error(f"Failed to get trade offer status: {e}")
            raise InternalServerError("Failed to get trade offer status.")
