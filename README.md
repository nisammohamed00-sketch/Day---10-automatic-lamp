# Day 10 - automatic-lamp
Day 10 use case deployment using functions with exception handling

Use Case Deployment Using Functions with Exception Handling
A practical example of deploying a function-based application with robust exception handling.

This project demonstrates how to build a serverless-style function that processes an order, validates its input, handles expected and unexpected errors, and returns consistent responses suitable for deployment behind an HTTP API.

**Use Case**

An e-commerce application receives an order request containing:

* A customer ID
* One or more products
* Product quantities


**The function must:**

* Validate the incoming request.
* Calculate the order total.
* Reject invalid products or quantities.
* Handle service failures gracefully.
* Return a predictable response for clients.
* Log unexpected errors without exposing sensitive implementation details.


**Example Project Structure**

```python

 ├── app.py
 ├── requirements.txt
 └── tests/
    └── test_app.py
```


**Function Implementation**

The following example uses Python and follows a structure that can be adapted to AWS Lambda, Azure Functions, Google Cloud Functions, or another function-as-a-service platform.


```python
 app.py

import json
import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


PRODUCT_CATALOG = {
    "keyboard": Decimal("49.99"),
    "mouse": Decimal("19.99"),
    "monitor": Decimal("199.99"),
}


class ValidationError(Exception):
    """Raised when the request contains invalid data."""


class ProductNotFoundError(Exception):
    """Raised when a requested product is not in the catalog."""


def calculate_order_total(items):
    """Calculate the total price for the requested items."""
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
    """Return a consistent HTTP-style response."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    """Process an order request.

    The function follows the common serverless handler signature:
    handler(event, context).
    """
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
        # Log the full traceback internally, but return a safe message to clients.
        logger.exception("Unexpected error while processing order")
        return response(500, {"error": "An internal server error occurred"})
```

Example Request

```python
{
  "customer_id": "customer-123",
  "items": [
    {
      "product": "keyboard",
      "quantity": 2
    },
    {
      "product": "mouse",
      "quantity": 1
    }
  ]
}
```

Example Successful Response

```python
{
  "statusCode": 200,
  "body": {
    "message": "Order processed successfully",
    "customer_id": "customer-123",
    "total": "119.97"
  }
}
```

Example Error Responses


Invalid JSON
```python
{
  "statusCode": 400,
  "body": {
    "error": "Request body must contain valid JSON"
  }
}
Missing Required Data

{
  "statusCode": 400,
  "body": {
    "error": "customer_id is required"
  }
}
```

Unknown Product
```python
{
  "statusCode": 404,
  "body": {
    "error": "unknown product: tablet"
  }
}
```
**Exception-Handling Strategy**

The function separates errors into four categories:

![reference image](/screenshot/picture.jpq)


Error type	Example	HTTP status	Handling approach
Malformed request	Invalid JSON	400	Return a clear client error
Validation error	Missing customer ID or invalid quantity	400	Explain what must be corrected
Missing resource	Product does not exist	404	Tell the client the resource was not found
Unexpected failure	Database or runtime failure	500	Log details internally and return a safe message
Recommended Practices
Catch specific exceptions before broad exceptions.
Avoid using except Exception as the only error-handling mechanism.
Log stack traces for unexpected failures.
Do not return stack traces, secrets, or internal infrastructure details to clients.
Use consistent response formats across all code paths.
Make errors observable through logs and monitoring alerts.
Keep business logic separate from the function handler when possible.
Use retries only for transient failures and make operations idempotent before enabling retries.
Local Setup
Requirements
Python 3.10 or later
pip
Install Dependencies
This example uses only the Python standard library, so no third-party packages are required. If you add dependencies, list them in requirements.txt and install them with:


pip install -r requirements.txt
Run Locally

python - <<'PY'
import json
from app import lambda_handler

request = {
    "body": json.dumps({
        "customer_id": "customer-123",
        "items": [
            {"product": "keyboard", "quantity": 2},
            {"product": "mouse", "quantity": 1},
        ],
    })
}

print(lambda_handler(request, None))
PY
Testing
A simple test suite can verify both success and failure paths.


# tests/test_app.py

import json

from app import lambda_handler


def make_event(payload):
    return {"body": json.dumps(payload)}


def test_successful_order():
    result = lambda_handler(
        make_event(
            {
                "customer_id": "customer-123",
                "items": [{"product": "keyboard", "quantity": 1}],
            }
        ),
        None,
    )

    assert result["statusCode"] == 200
    assert json.loads(result["body"])["total"] == "49.99"


def test_missing_customer_id():
    result = lambda_handler(
        make_event({"items": [{"product": "mouse", "quantity": 1}]}),
        None,
    )

    assert result["statusCode"] == 400


def test_unknown_product():
    result = lambda_handler(
        make_event(
            {
                "customer_id": "customer-123",
                "items": [{"product": "tablet", "quantity": 1}],
            }
        ),
        None,
    )

    assert result["statusCode"] == 404
Run the tests with:


pytest
Deployment Example: AWS Lambda
The handler is named lambda_handler in app.py, so the AWS Lambda handler value should be:


app.lambda_handler
A typical deployment flow is:

Create a Lambda function using a supported Python runtime.
Upload app.py and any dependencies.
Configure an API Gateway HTTP endpoint.
Set the integration target to the Lambda function.
Configure logging and monitoring.
Test successful requests and each expected error path.
Add alarms for repeated 5xx responses and function errors.
For a packaged deployment, create a ZIP archive containing the function and dependencies:


mkdir package
pip install -r requirements.txt -t package/
cp app.py package/
cd package
zip -r ../function.zip .
Upload function.zip to the function deployment configuration.

The exact deployment command depends on the cloud provider, permissions model, region, runtime, and infrastructure tool used by your project.

Production Considerations
Input Validation
Validate all external input at the function boundary. Never assume that a client, API gateway, or upstream service has already validated the request.

Observability
Capture:

Request correlation IDs
Function duration
Error counts
Cold-start or initialization failures
Downstream service failures
Avoid logging sensitive customer data or authentication credentials.

Retry Safety
If the platform retries a failed invocation, the function should not create duplicate orders. Use an idempotency key or persistent request ID when the operation has side effects.

Timeouts
Set function and downstream service timeouts deliberately. A timeout should produce a controlled error and should not leave resources or transactions in an inconsistent state.

Configuration
Store environment-specific values such as catalog URLs, database credentials, and API keys in environment variables or a managed secrets service rather than hard-coding them.

Summary
This example shows how a deployed function can:

Process a real business use case.
Validate input before performing business logic.
Handle expected exceptions explicitly.
Protect clients from internal error details.
Log unexpected failures for diagnosis.
Return predictable HTTP-style responses.
Be tested and deployed as a serverless function.