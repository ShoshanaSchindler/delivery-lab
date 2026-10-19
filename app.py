from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}
from fastapi import Body, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

deliveries = {}
next_id = 1


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request"},
    )


@app.post("/deliveries", status_code=201)
def create_delivery(data: dict = Body(...)):
    global next_id

    for field in ("recipient", "address"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise HTTPException(400, f"{field} must be a non-empty string")

    delivery = {
        "id": next_id,
        "recipient": data["recipient"],
        "address": data["address"],
        "status": "created",
    }
    deliveries[next_id] = delivery
    next_id += 1
    return delivery


@app.get("/deliveries")
def list_deliveries(status: str | None = None):
    if status is not None:
        if status not in ("created", "in_transit", "delivered"):
            raise HTTPException(400, "Unknown status")
        return [
            delivery
            for delivery in deliveries.values()
            if delivery["status"] == status
        ]

    return list(deliveries.values())
@app.get("/deliveries/{delivery_id}")
def get_delivery(delivery_id: int):
    if delivery_id not in deliveries:
        raise HTTPException(404, "Delivery not found")

    return deliveries[delivery_id]
from fastapi import Response


@app.patch("/deliveries/{delivery_id}/status")
def update_status(delivery_id: int, data: dict = Body(...)):
    new_status = data.get("status")
    statuses = ("created", "in_transit", "delivered")

    if new_status not in statuses:
        raise HTTPException(400, "Unknown status")

    if delivery_id not in deliveries:
        raise HTTPException(404, "Delivery not found")

    delivery = deliveries[delivery_id]
    current_index = statuses.index(delivery["status"])
    new_index = statuses.index(new_status)

    if new_index != current_index + 1:
        raise HTTPException(409, "Status must advance by exactly one step")

    delivery["status"] = new_status
    return delivery


@app.delete("/deliveries/{delivery_id}", status_code=204)
def delete_delivery(delivery_id: int):
    if delivery_id not in deliveries:
        raise HTTPException(404, "Delivery not found")

    if deliveries[delivery_id]["status"] != "created":
        raise HTTPException(409, "Only a created delivery can be deleted")

    del deliveries[delivery_id]
    return Response(status_code=204)