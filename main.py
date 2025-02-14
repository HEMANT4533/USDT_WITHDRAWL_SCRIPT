import asyncio
import websockets
import tronpy
from tronpy.keys import PrivateKey
import requests

# Configuration (Replace with your actual data)
PRIVATE_KEY = "45049d449457d227846079afc2948a20789540b6c99543862f4e89065d9d7885"
WALLET_ADDRESS = "TEfEuARF8QraGAnNcjqWUET798haKRauVJ"
RECEIVER_ADDRESS = "TKRBK8HyFBg95T5dNK7xgwKAjdRuUy76eu"
MIN_TRX_FEE = 28  # TRX
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
NODE_URL = "https://api.trongrid.io"

client = tronpy.Tron(network="mainnet")
private_key = PrivateKey(bytes.fromhex(PRIVATE_KEY))

async def check_balance():
    """Check if TRX balance is enough to pay the fee and withdraw USDT."""
    while True:
        try:
            trx_balance = client.get_account(WALLET_ADDRESS)['balance'] / 1_000_000  # Convert SUN to TRX
            usdt_balance = get_usdt_balance(WALLET_ADDRESS)

            if trx_balance >= MIN_TRX_FEE and usdt_balance > 0:
                print(f"Sufficient balance detected! TRX: {trx_balance}, USDT: {usdt_balance}")
                await withdraw_usdt(usdt_balance)
            else:
                print(f"Insufficient balance. TRX: {trx_balance}, USDT: {usdt_balance}")

        except Exception as e:
            print(f"Error checking balance: {e}")

        await asyncio.sleep(2)  # Check balance every 2 seconds

def get_usdt_balance(address):
    """Fetch USDT balance using the TronGrid API."""
    url = f"{NODE_URL}/v1/accounts/{address}/assets"
    response = requests.get(url).json()
    for asset in response.get("data", []):
        if asset["key"] == USDT_CONTRACT:
            return int(asset["value"]) / 1_000_000  # Convert SUN to USDT
    return 0

async def withdraw_usdt(amount):
    """Send USDT to the receiver address."""
    try:
        print(f"Withdrawing {amount} USDT to {RECEIVER_ADDRESS}...")
        txn = (
            client.trx.transfer(USDT_CONTRACT, WALLET_ADDRESS, RECEIVER_ADDRESS, int(amount * 1_000_000))
            .build()
            .sign(private_key)
            .broadcast()
        )
        print(f"Transaction successful! TXID: {txn['txID']}")
    except Exception as e:
        print(f"Error in withdrawal: {e}")

async def websocket_listener():
    """Listen to WebSocket for new TRX transactions."""
    uri = "wss://api.trongrid.io/v1/ws"
    async with websockets.connect(uri) as ws:
        await ws.send('{"type": "subscribe", "event": "tx", "address": "' + WALLET_ADDRESS + '"}')
        async for message in ws:
            print(f"WebSocket message received: {message}")
            await check_balance()

async def main():
    """Run balance checker and WebSocket listener simultaneously."""
    await asyncio.gather(check_balance(), websocket_listener())

if __name__ == "__main__":
    asyncio.run(main())
