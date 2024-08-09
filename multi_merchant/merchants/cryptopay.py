from __future__ import annotations

import datetime
import typing
from typing import Literal, Any

from CryptoPayAPI import CryptoPay as CryptoPayAPI, schemas
from pydantic import validator, field_serializer

from .base import BaseMerchant, MerchantEnum, PAYMENT_LIFETIME
from ..models import Invoice


class CryptoPay(BaseMerchant):
    cp: CryptoPayAPI | None = None
    merchant: Literal[MerchantEnum.CRYPTO_PAY]

    @validator('cp', always=True)
    def validate_cp(cls, v, values):
        return v or CryptoPayAPI(values.get("api_key").get_secret_value())

    @field_serializer('cp')
    def serialize_cp(cp: CryptoPayAPI | None) -> Any:
        return None

    async def create_invoice(
            self,
            user_id: int,
            amount: int | float | str,
            InvoiceClass: typing.Type[Invoice],

            currency: schemas.Assets = schemas.Assets.USDT,
            description: str | None = None,
            **kwargs
    ) -> Invoice:
        invoice = await self.cp.create_invoice(
            asset=currency,
            amount=amount,
            description=description,
            # paid_btn_name=PaidButtonNames.VIEW_ITEM,
            # paid_btn_url='https://example.com'
        )
        expired_at = datetime.datetime.now() + datetime.timedelta(seconds=PAYMENT_LIFETIME)

        return InvoiceClass(
            user_id=user_id,
            amount=amount,
            currency=currency,
            invoice_id=invoice.invoice_id,
            pay_url=invoice.pay_url,
            description=description,
            merchant=self.merchant,
            expire_at=expired_at
        )

    async def is_paid(self, invoice_id: str) -> bool:
        invoices = await self.cp.get_invoices(
            invoice_ids=invoice_id,
            status=schemas.InvoiceStatus.PAID
        )
        return invoices[0].status == schemas.InvoiceStatus.PAID
