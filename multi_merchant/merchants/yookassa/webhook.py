import typing
from enum import StrEnum

from aiohttp import web
from aiohttp.web_routedef import AbstractRouteDef
from pydantic import BaseModel


class Amount(BaseModel):
    value: str
    currency: str


class Recipient(BaseModel):
    account_id: str
    gateway_id: str


class PaymentMethod(BaseModel):
    type: str
    id: str
    saved: bool
    title: str
    account_number: str


class PaymentObject(BaseModel):
    id: str
    status: str
    amount: Amount
    income_amount: Amount
    description: str
    recipient: Recipient
    payment_method: PaymentMethod
    captured_at: str
    created_at: str
    test: bool = False  # Значение по умолчанию
    refunded_amount: Amount
    paid: bool = False  # Значение по умолчанию
    refundable: bool = False  # Значение по умолчанию
    metadata: dict = {}  # Пустой словарь по умолчанию


class EventType(StrEnum):
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_WAITING_FOR_CAPTURE = "payment.waiting_for_capture"
    PAYMENT_CANCELED = "payment.canceled"
    PAYMENT_REFUNDED = "payment.refunded"
    PAYMENT_PENDING = "payment.pending"


class Notification(BaseModel):
    type: str
    event: str
    object: PaymentObject


async def start_server(
        routes: typing.Iterable[AbstractRouteDef],
        host: str = "0.0.0.0",
        port: int = 85
):
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        host,
        port,
    )
    await site.start()
