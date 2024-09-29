from typing import Annotated

from pydantic import Field
from multi_merchant.merchants.base import BaseMerchant, MerchantEnum, MerchantUnion
from multi_merchant.merchants.aaio.merchant import AaioPay
from multi_merchant.merchants.betatransfer import BetaTransferPay
from multi_merchant.merchants.cryptocloud import CryptoCloud
from multi_merchant.merchants.cryptomus import Cryptomus
from multi_merchant.merchants.cryptopay import CryptoPay
from multi_merchant.merchants.payok.merchant import PayokPay
from multi_merchant.merchants.qiwi import Qiwi
from multi_merchant.merchants.yookassa.merchant import YooKassa
from multi_merchant.merchants.yoomoney.merchant import YooMoney
from multi_merchant.models.invoice import Invoice, Currency, Status


MerchantAnnotated = Annotated[
    Qiwi
    | YooKassa
    | YooMoney
    | CryptoPay
    | CryptoCloud
    | Cryptomus
    | BetaTransferPay
    | PayokPay
    | AaioPay,
    Field(discriminator="merchant"),
]


BaseInvoice = Invoice
__all__ = (
    "BaseMerchant",
    "MerchantAnnotated",
    "MerchantEnum",
    "MerchantUnion",
    "Qiwi",
    "YooKassa",
    "YooMoney",
    "CryptoPay",
    "CryptoCloud",
    "Cryptomus",
    "BetaTransferPay",
    "PayokPay",
    "AaioPay",
    "BaseInvoice",
    "Currency",
    "Status",
)
