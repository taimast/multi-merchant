import asyncio
from pprint import pprint

from CryptoPayAPI import CryptoPay
from CryptoPayAPI.schemas import Assets, PaidButtonNames, InvoiceStatus, Invoice
from aiohttp import web

routes = web.RouteTableDef()
cp = CryptoPay('7293:AAlLHf1shXQTQFe1THy8iU8DalVZYy6D5bI', testnet=True)


@routes.post("/")
async def handle(request: web.Request):
    """Handle request"""
    body = await request.read()
    headers = dict(request.raw_headers)
    print(await request.text())
    update = await cp.process_webhook_update(body, headers)
    print(f'Recieved {update.payload.amount} {update.payload.asset}!')
    return web.Response()


async def start_server():
    app = web.Application()
    app.add_routes(routes)
    # web.run_app(
    #     app,
    #     host="0.0.0.0",
    #     port=8001,
    #     loop=asyncio.get_event_loop(),
    # )
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        "0.0.0.0",
        8001,
    )
    await site.start()


async def wait(invoice: Invoice):
    while True:
        invoices = await cp.get_invoices(
            invoice_ids=f"{invoice.invoice_id}",
            status=InvoiceStatus.PAID
        )
        for invoice in invoices:
            pprint(invoice.dict())
        await asyncio.sleep(1)


async def main():
    invoice = await cp.create_invoice(
        asset=Assets.USDT,
        amount=0.5,
        description='test',
        paid_btn_name=PaidButtonNames.VIEW_ITEM,
        paid_btn_url='https://example.com'
    )
    pprint(invoice.dict())
    # await wait(invoice)
    await start_server()
    await asyncio.Future()


if __name__ == '__main__':
    asyncio.run(main())
