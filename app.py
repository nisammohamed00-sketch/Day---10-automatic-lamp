import json
import logging
from decimal import Decimal, InvalidOperation

from flask import Flask, request, jsonify

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


PRODUCT_CATALOG = {
    "keyboard": Decimal("49.99"),
    "mouse": Decimal("19.99"),
    "monitor": Decimal("199.99"),
}


class ValidationError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


def calculate_order_total(items):
    if not isinstance(items, list) or not items:
        raise ValidationError("items must be a non-empty list")

    total = Decimal("0.00")

    for item in items:
        if not isinstance(item, dict):
            raise ValidationError("each item must be an object")

        product = item.get("product")
        quantity = item.get("quantity")

        if product not in PRODUCT_CATALOG:
            raise ProductNotFoundError(f"unknown product: {product}")

        if not isinstance(quantity, int) or quantity <= 0:
            raise ValidationError("quantity must be a positive integer")

        total += PRODUCT_CATALOG[product] * quantity

    return total.quantize(Decimal("0.01"))


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    try:
        raw_body = event.get("body", "{}")
        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body

        customer_id = body.get("customer_id")
        if not customer_id:
            raise ValidationError("customer_id is required")

        total = calculate_order_total(body.get("items"))

        logger.info("Order calculated successfully for customer %s", customer_id)

        return response(
            200,
            {
                "message": "Order processed successfully",
                "customer_id": customer_id,
                "total": str(total),
            },
        )

    except json.JSONDecodeError:
        return response(400, {"error": "Request body must contain valid JSON"})

    except ValidationError as error:
        return response(400, {"error": str(error)})

    except ProductNotFoundError as error:
        return response(404, {"error": str(error)})

    except (InvalidOperation, ValueError) as error:
        logger.warning("Invalid numeric value: %s", error)
        return response(400, {"error": "Request contains an invalid numeric value"})

    except Exception:
        logger.exception("Unexpected error while processing order")
        return response(500, {"error": "An internal server error occurred"})


app = Flask(__name__)


@app.route("/order", methods=["POST"])
def order():
    event = {"body": request.get_data(as_text=True)}
    res = lambda_handler(event, None)
    body = json.loads(res.get("body")) if isinstance(res.get("body"), str) else res.get("body")
    return (jsonify(body), res.get("statusCode", 200), res.get("headers", {}))


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
