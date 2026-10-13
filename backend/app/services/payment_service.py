import random
import string


class PaymentService:
    """Mock payment gateway — in a real system this would call an external PSP."""

    def charge(self, amount: float, pnr: str) -> dict:
        txn_id = "TXN" + "".join(random.choices(string.digits, k=10))
        return {"txn_id": txn_id, "amount": amount, "pnr": pnr, "status": "PAID"}

    def refund(self, amount: float, pnr: str) -> dict:
        txn_id = "RFD" + "".join(random.choices(string.digits, k=10))
        return {"txn_id": txn_id, "amount": amount, "pnr": pnr, "status": "REFUNDED"}
