from __future__ import annotations

import datetime
import typing
import uuid
from base64 import b64encode
from enum import Enum
from typing import Optional, Literal

from pydantic import BaseModel, validator

from multi_merchant.merchants.base import (
    BaseMerchant,
    Currency,
    InvoiceT,
    MerchantEnum,
    PAYMENT_LIFETIME,
    MerchantUnion,
    Amount as BaseAmount,
)
from multi_merchant.models import Invoice


class Amount(BaseModel):
    currency: str
    value: str


class Confirmation(BaseModel):
    confirmation_url: Optional[str] = None
    type: str = "redirect"


class ConfirmationRequest(BaseModel):
    return_url: Optional[str] = None
    type: str = "redirect"


class Recipient(BaseModel):
    account_id: str
    gateway_id: str


class Status(str, Enum):
    WAITING_FOR_CAPTURE = "waiting_for_capture"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    PENDING = "pending"


class Customer(BaseModel):
    email: str


class Item(BaseModel):
    description: str = "Товар"
    quantity: int = 1
    amount: Amount = Amount(currency="RUB", value="250.0")
    vat_code: int = 1
    payment_subject: str = "commodity"
    payment_mode: str = "full_payment"


class Receipt(BaseModel):
    customer: Customer = Customer(email="some@gmail.com")
    items: list[Item] = [Item()]


class YooPaymentRequest(BaseModel):
    amount: Amount
    description: str | None = None
    confirmation: ConfirmationRequest | None = None
    capture: bool = True
    receipt: Receipt | None = None
    metadata: dict | None = None

    # необязательный expire_at. Не указано в документации. Всегда равен 1 часу
    # "expires_at": str(datetime.datetime.now(TIME_ZONE) + datetime.timedelta(minutes=15))

    @validator("description", always=True)
    def description_validator(cls, v, values):
        if not v:
            v = f"Product {values.get('amount')}"
        return v

    @classmethod
    def create_payment(
        cls,
        amount: int | float | str,
        currency: str,
        metadata: dict | None = None,
        return_url: str | None = None,
        description: str | None = None,
    ) -> typing.Self:
        return cls(
            amount=Amount(currency=currency, value=str(amount)),
            confirmation=ConfirmationRequest(return_url=return_url),
            description=description,
            receipt=Receipt(
                items=[Item(amount=Amount(currency=currency, value=str(float(amount))))]
            ),
            metadata=metadata,
        )


class YooPayment(YooPaymentRequest):
    id: uuid.UUID
    created_at: datetime.datetime
    confirmation: Confirmation | None = None
    paid: bool
    status: Status
    recipient: Recipient | None = None
    income_amount: Amount | None = None
    metadata: dict | None = None

    def is_paid(self) -> bool:
        return self.paid


class YooKassa(BaseMerchant):
    create_url: Optional[str] = "https://api.yookassa.ru/v3/payments"
    merchant: Literal[MerchantEnum.YOOKASSA] = MerchantEnum.YOOKASSA

    @property
    def headers(self) -> dict:
        user_and_pass = b64encode(
            f"{self.shop_id}:{self.api_key.get_secret_value()}".encode()
        ).decode("ascii")
        return {
            "Authorization": f"Basic {user_and_pass}",
            "Content-type": "application/json",
        }

    async def create_invoice(
        self,
        user_id: int,
        amount: BaseAmount,
        InvoiceClass: typing.Type[InvoiceT],
        currency: Currency = Currency.RUB,
        description: str | None = None,
        return_url: str = "https://t.me/",  # todo L2 14.08.2022 19:02 taima: прописать url
    ) -> InvoiceT:
        description = description or f"Product {amount} {currency} for user ID{user_id}"
        data = YooPaymentRequest.create_payment(
            amount=amount,
            currency=currency,
            return_url=return_url,
            description=description,
        )

        idempotence_key = {"Idempotence-Key": str(uuid.uuid4())}
        response = await self.make_request(
            "POST",
            self.create_url,
            json=data.model_dump(),
            headers=idempotence_key,
        )
        if response.get("type") == "error":
            raise Exception(response)
        yoo_payment = YooPayment(**response)
        return InvoiceClass(
            user_id=user_id,
            amount=float(yoo_payment.amount.value),
            currency=yoo_payment.amount.currency,
            invoice_id=str(yoo_payment.id),
            pay_url=yoo_payment.confirmation.confirmation_url,
            description=description,
            merchant=self.merchant,
            expire_at=datetime.datetime.now() + datetime.timedelta(seconds=PAYMENT_LIFETIME),
        )

    async def is_paid(self, invoice_id: str) -> bool:
        """Проверка статуса платежа"""
        return (await self.get_invoice(invoice_id)).paid

    async def get_invoice(self, invoice_id: str) -> YooPayment:
        """Получение информации о платеже"""
        res = await self.make_request("GET", f"{self.create_url}/{invoice_id}")
        return YooPayment.parse_obj(res)

    async def cancel(self, bill_id: uuid.UUID) -> YooPayment:
        """Отмена платежа"""
        idempotence_key = {"Idempotence-Key": str(uuid.uuid4())}
        res = await self.make_request(
            "POST", f"{self.create_url}/{bill_id}/cancel", headers=idempotence_key
        )
        return YooPayment.parse_obj(res)
