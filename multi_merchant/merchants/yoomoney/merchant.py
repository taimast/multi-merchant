from __future__ import annotations

import asyncio
import datetime
import typing
from typing import Any, Literal, Optional
import uuid

from pydantic import model_validator

from ..base import (
    Amount,
    BaseMerchant,
    Currency,
    InvoiceT,
    MerchantEnum,
    PAYMENT_LIFETIME,
    MerchantUnion,
)
from yoomoney import Client, Quickpay
from ...models import Invoice


class YooMoney(BaseMerchant):
    client: Client
    receiver: Optional[str] = None
    merchant: Literal[MerchantEnum.YOOMONEY]

    @model_validator(mode="before")
    @classmethod
    def initialize_client(cls, values: Any):
        if isinstance(values, dict):
            api_key = values.get("api_key")
            if api_key:
                values["client"] = Client(token=api_key)
        return values

    def get_receiver(self) -> str:
        if self.receiver:
            return self.receiver

        account_info = self.client.account_info()
        accoint_number: str = account_info.account_number  # type: ignore
        self.receiver = accoint_number
        return self.receiver

    def create_quickpay(
        self,
        amount: float,
        invoive_id: str,
        description: str = "Sponsor this project",
    ) -> Quickpay:
        receiver = self.get_receiver()
        qp = Quickpay(
            receiver=receiver,
            quickpay_form="shop",
            targets=description,
            paymentType="SB",
            sum=amount,
            label=invoive_id,
            comment=description,
        )
        return qp

    async def create_invoice(
        self,
        user_id: int,
        amount: Amount,
        InvoiceClass: typing.Type[InvoiceT],
        currency: str = "RUB",
        description: str | None = None,
        return_url: str = "https://t.me/",  # todo L2 14.08.2022 19:02 taima: прописать url
    ) -> InvoiceT:
        invoive_id = str(uuid.uuid4())
        amount = float(amount)

        description = description or f"Sponsor this project {invoive_id}"
        qp = await asyncio.to_thread(self.create_quickpay, amount, invoive_id, description)

        return InvoiceClass(
            user_id=user_id,
            amount=amount,
            currency=currency,
            invoice_id=invoive_id,
            pay_url=qp.redirected_url,
            description=description,
            merchant=self.merchant,
            expire_at=datetime.datetime.now() + datetime.timedelta(seconds=PAYMENT_LIFETIME),
        )

    async def is_paid(self, invoice_id: str) -> bool:
        """Проверка статуса платежа"""
        operations = await self.get_operations(invoice_id)
        if operations and operations[0].status == "success":
            return True
        return False

    async def get_operations(self, invoice_id: str):
        history = await asyncio.to_thread(
            self.client.operation_history,
            label=invoice_id,
        )
        return history.operations
