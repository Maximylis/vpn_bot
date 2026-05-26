from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class VpnKeyCreate(BaseModel):
    user_id: int
    provider: str = "manual"
    key_name: str | None = None
    config_text: str


class VpnKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    provider: str
    key_name: str | None
    config_text: str
    status: str
    created_at: datetime
    revoked_at: datetime | None


class SubscriptionCreate(BaseModel):
    user_id: int
    starts_at: datetime
    expires_at: datetime
    is_trial: bool = False


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    starts_at: datetime
    expires_at: datetime
    created_at: datetime
    is_trial: bool
    trial_penultimate_day_notified: bool
    trial_lastday_notified: bool
    auto_renew: bool
    payment_method_id: str | None
    auto_renew_tariff: str | None


class UserAccessRead(BaseModel):
    has_access: bool
    reason: str | None = None
    user: UserRead | None = None
    subscription: SubscriptionRead | None = None
    vpn_keys: list[VpnKeyRead] = []


class GrantAccessRead(BaseModel):
    ok: bool
    reason: str | None = None
    user: UserRead | None = None
    subscription: SubscriptionRead | None = None
    vpn_key: VpnKeyRead | None = None


class PaymentCreateRequest(BaseModel):
    telegram_id: int
    tariff: str


class PaymentCreateResponse(BaseModel):
    ok: bool
    payment_id: int
    yookassa_payment_id: str
    confirmation_url: str


class YookassaWebhookObject(BaseModel):
    id: str


class YookassaWebhookRequest(BaseModel):
    type: str
    event: str
    object: YookassaWebhookObject
