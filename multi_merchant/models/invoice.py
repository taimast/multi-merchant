from __future__ import annotations

import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Optional, Self

from sqlalchemy import String, func, select, JSON
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, selectinload

from multi_merchant.merchants.base import MerchantEnum, PAYMENT_LIFETIME


# класс с методами для работы с мерчантами


class Currency(StrEnum):
    """Currency codes."""

    USD = "USD"
    RUB = "RUB"
    EUR = "EUR"
    GBP = "GBP"

    USDT = "USDT"
    BTC = "BTC"
    TON = "TON"
    ETH = "ETH"
    USDC = "USDC"
    BUSD = "BUSD"


class Status(StrEnum):
    """Invoice status."""

    PENDING = "pending"
    SUCCESS = "success"
    EXPIRED = "expired"
    FAIL = "fail"


class Invoice:
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)

    currency: Mapped[str | None]
    amount: Mapped[float | None]
    invoice_id: Mapped[str] = mapped_column(String(50), index=True)
    expire_at: Mapped[datetime.datetime | None] = mapped_column(
        default=lambda: datetime.datetime.now() + datetime.timedelta(seconds=PAYMENT_LIFETIME)
    )
    extra_data: Mapped[dict] = mapped_column(JSON, default={})
    pay_url: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[Status | None] = mapped_column(String(10), default=Status.PENDING)

    # CryptoCloud
    order_id: Mapped[str | None] = mapped_column(String(50), index=True, doc="Custom product ID")
    email: Mapped[str | None] = mapped_column(String(50), index=True, doc="Customer email")

    # CryptoPay, YooKassa, Qiwi
    description: Mapped[str | None] = mapped_column(String(255))

    merchant: Mapped[MerchantEnum | None]

    if TYPE_CHECKING:

        def __init__(
            self,
            user_id: int,
            amount: float,
            currency: str,
            invoice_id: str,
            pay_url: Optional[str] = None,
            description: Optional[str] = None,
            merchant: Optional[MerchantEnum] = None,
            expire_at: Optional[datetime.datetime] = None,
            extra_data: dict = {},
            status: Status = Status.PENDING,
            order_id: Optional[str] = None,
            email: Optional[str] = None,
        ): ...

    def __str__(self):
        return f"[{self.__class__.__name__}] {self.user} {self.amount} {self.currency}"

    @classmethod
    async def get_pending_invoices(cls, session: AsyncSession) -> list[Self]:
        """Get pending invoices."""
        result = await session.execute(
            select(cls)
            .options(selectinload(cls.user))
            .where(cls.expire_at > func.now())
            .where(cls.status == Status.PENDING)
        )
        return result.unique().scalars().all()

    @classmethod
    async def get_last_invoice(
        cls,
        session: AsyncSession,
        user_id: int,
        amount: int | float | str,
        currency: Currency,
        merchant: MerchantEnum,
    ) -> Self | None:
        """Get last unpaid invoice."""
        return (
            (
                await session.execute(
                    select(cls)
                    .where(cls.user_id == user_id)
                    .where(cls.amount == float(amount))
                    .where(cls.currency == currency)
                    .where(cls.merchant == merchant)
                    .where(cls.status == Status.PENDING)
                    .where(cls.expire_at > func.now())
                    .order_by(cls.id.desc())
                )
            )
            .unique()
            .scalar_one_or_none()
        )

    # todo L1 TODO 22.04.2023 22:56 taima: Do successfully_paid and check_payment methods in one method
    async def successfully_paid(self):
        """Successful payment."""
        self.status = Status.SUCCESS
