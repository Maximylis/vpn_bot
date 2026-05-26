import uuid

from yookassa import Configuration, Payment

from app.config import settings


Configuration.account_id = settings.yookassa_shop_id
Configuration.secret_key = settings.yookassa_secret_key


def create_yookassa_payment(
    amount: str,
    description: str,
    telegram_id: int,
    tariff: str,
) -> Payment:
    return Payment.create({
        "amount": {
            "value": amount,
            "currency": "RUB",
        },
        "confirmation": {
            "type": "redirect",
            "return_url": settings.yookassa_return_url,
        },
        "capture": True,
        "save_payment_method": True,
        "description": description,
        "receipt": {
            "customer": {
                "email": "support@okvpn.example",
            },
            "items": [
                {
                    "description": description,
                    "quantity": "1.00",
                    "amount": {
                        "value": amount,
                        "currency": "RUB",
                    },
                    "vat_code": 1,
                    "payment_mode": "full_payment",
                    "payment_subject": "service",
                }
            ],
        },
        "metadata": {
            "telegram_id": str(telegram_id),
            "tariff": tariff,
        },
    }, uuid.uuid4())


def get_yookassa_payment(payment_id: str) -> Payment:
    return Payment.find_one(payment_id)
