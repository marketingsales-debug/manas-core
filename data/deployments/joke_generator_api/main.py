from fastapi import FastAPI, Depends, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import httpx
import base64
import json
from typing import Optional

app = FastAPI()

SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
MIN_PAYMENT_AMOUNT = 0.01
PAYMENT_ADDRESS = "44kbejjDb4fN52hDhR1QygvtNsaEyjev2ucMd4HvkgMZ"

jokes = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "What do you call a fake noodle? An impasta!",
    "How do you organize a space party? You planet!",
    "Why did the bicycle fall over? Because it was two-tired!",
    "What's brown and sticky? A stick!",
    "Why can't you explain puns to kleptomaniacs? They always take things literally.",
    "What's the best time to go to the dentist? Tooth-hurty!",
    "How do you make a tissue dance? Put a little boogie in it!",
    "Why did the math book look sad? Because it had too many problems."
]

async def verify_solana_payment(x_payment_signature: Optional[str] = Header(None)):
    if not x_payment_signature:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Payment Required",
                "message": f"Please send at least {MIN_PAYMENT_AMOUNT} SOL to {PAYMENT_ADDRESS} and include the transaction signature in the X-Payment-Signature header"
            }
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                SOLANA_RPC_URL,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [
                        x_payment_signature,
                        {"encoding": "jsonParsed"}
                    ]
                }
            )
            response.raise_for_status()
            transaction_data = response.json()

            if "result" not in transaction_data:
                raise HTTPException(status_code=402, detail={"error": "Invalid transaction signature"})

            transaction = transaction_data["result"]
            if not transaction:
                raise HTTPException(status_code=402, detail={"error": "Transaction not found"})

            meta = transaction.get("meta", {})
            if meta.get("err"):
                raise HTTPException(status_code=402, detail={"error": "Transaction failed"})

            post_balances = meta.get("postBalances", [])
            pre_balances = meta.get("preBalances", [])

            if len(post_balances) < 2 or len(pre_balances) < 2:
                raise HTTPException(status_code=402, detail={"error": "Invalid transaction structure"})

            account_index = None
            for i, account in enumerate(transaction["transaction"]["message"]["accountKeys"]):
                if account["pubkey"] == PAYMENT_ADDRESS:
                    account_index = i
                    break

            if account_index is None:
                raise HTTPException(status_code=402, detail={"error": "Payment address not involved in transaction"})

            post_balance = post_balances[account_index]
            pre_balance = pre_balances[account_index]

            amount_paid = (post_balance - pre_balance) / 1e9

            if amount_paid < MIN_PAYMENT_AMOUNT:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "Insufficient payment",
                        "required": MIN_PAYMENT_AMOUNT,
                        "received": amount_paid
                    }
                )

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=402, detail={"error": "Failed to verify payment", "details": str(e)})
        except Exception as e:
            raise HTTPException(status_code=402, detail={"error": "Payment verification failed", "details": str(e)})

@app.get("/joke", dependencies=[Depends(verify_solana_payment)])
async def get_joke():
    import random
    return {"joke": random.choice(jokes)}

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Joke Generator API",
        "instructions": f"Send a GET request to /j