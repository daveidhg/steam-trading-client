from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest, InternalServerError

from app.services.steam_client import steam_client_service

trade_bp = Blueprint("trade", __name__)


@trade_bp.route("/create-offer", methods=["POST"])
def create_offer():
    """
    Create a new trade offer to a partner Steam user.
    Request body:
    {
        "partner_steam_id": "76561198000000000",
        "asset_ids": ["1234567890", "9876543210"]
    }
    """
    data = request.get_json()

    if not data:
        raise BadRequest("Missing JSON body.")

    required_fields = ["partner_steam_id", "asset_ids"]
    for field in required_fields:
        if field not in data:
            raise BadRequest(f"Missing required field: {field}")

    partner_steam_id = data["partner_steam_id"]
    asset_ids = data["asset_ids"]

    try:
        offer_id = steam_client_service.send_trade_offer(
            partner_steam_id=partner_steam_id,
            asset_ids=asset_ids
        )

        return jsonify({
            "success": True,
            "offer_id": offer_id
        }), 200

    except Exception as e:
        print(f"[ERROR] Failed to create trade offer: {e}")
        raise InternalServerError("Failed to create trade offer.")


@trade_bp.route("/cancel-offer", methods=["POST"])
def cancel_offer():
    """
    Cancel an existing trade offer.
    Request body:
    {
        "offer_id": "1234567890"
    }
    """
    data = request.get_json()

    if not data or "offer_id" not in data:
        raise BadRequest("Missing required field: offer_id")

    offer_id = data["offer_id"]

    try:
        success = steam_client_service.cancel_trade_offer(offer_id)

        return jsonify({
            "success": success,
            "offer_id": offer_id
        }), 200

    except Exception as e:
        print(f"[ERROR] Failed to cancel trade offer: {e}")
        raise InternalServerError("Failed to cancel trade offer.")


@trade_bp.route("/offer-status/<offer_id>", methods=["GET"])
def offer_status(offer_id):
    """
    Get status of an existing trade offer.
    """

    try:
        status = steam_client_service.get_offer_status(offer_id)

        return jsonify({
            "success": True,
            "offer_id": offer_id,
            "status": status
        }), 200

    except Exception as e:
        print(f"[ERROR] Failed to get trade offer status: {e}")
        raise InternalServerError("Failed to get trade offer status.")
