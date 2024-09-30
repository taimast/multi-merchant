from __future__ import annotations

import asyncio
import typing
import uuid
from typing import Literal, Optional, Any

from pydantic import Field, validator

from .base import BaseMerchant, MerchantEnum, MerchantUnion
from ..models.invoice import Invoice, Currency
from pyCryptomusAPI import Invoice as CryptomusInvoice, pyCryptomusAPI


class Cryptomus(BaseMerchant):
    merchant: Literal[MerchantEnum.CRYPTOMUS]

    create_url: Optional[str] = "https://api.cryptomus.com/v1/payment"
    status_url: Optional[str] = "https://api.cryptomus.com/v1/payment/info"
    client: Optional[pyCryptomusAPI] = Field(None, validate_default=True)

    @validator("client", always=True)
    def validate_client(cls, v, values):
        if v is None:
            merchant_uuid = values.get("shop_id")
            payment_api_key = values.get("api_key").get_secret_value()
            return pyCryptomusAPI(merchant_uuid, payment_api_key)
        return v

    async def create_invoice(
        self,
        user_id: int,
        amount: int | float | str,
        InvoiceClass: typing.Type[Invoice],
        currency: Currency = Currency.USD,
        description: str | None = None,
        **kwargs,
    ) -> Invoice:
        order_id = uuid.uuid4().hex

        invoice: CryptomusInvoice = await asyncio.to_thread(  # type: ignore
            self.client.create_invoice,
            amount=amount,
            currency=currency,
            order_id=order_id,
        )

        return InvoiceClass(
            user_id=user_id,
            amount=float(amount),
            currency=currency,
            invoice_id=invoice.order_id,  # type: ignore
            pay_url=invoice.url,
            description=description,
            merchant=self.merchant,
        )

    async def is_paid(self, invoice_id: str) -> bool:
        invoice: CryptomusInvoice = await asyncio.to_thread(  # type: ignore
            self.client.payment_information,
            order_id=invoice_id,
        )
        return bool(invoice.is_final)
