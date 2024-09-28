# MultiMerchant

## Конфигурация

```python
from multi_merchant import PayokPay

config = PayokPay(
    api_id=1,
    secret="secret",
    merchant=PayokPay.merchant,
    api_key="api_key",
    shop=1,
)
```

## Использование

```python
from multi_merchant import PayokPay

async def main():
    invoice = await config.create_invoice(
        user_id=1,
        amount=100,
        currency="RUB",
        description="Test Order",
        email="test@example.com",
    )
    print(invoice)
    await asyncio.sleep(10)
    print(await config.is_paid(invoice.invoice_id))


if __name__ == '__main__':
    asyncio.run(main())
```
