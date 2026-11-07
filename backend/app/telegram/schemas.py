"""Modelos pydantic para os poucos campos do Update da Bot API que o Solano usa."""

from pydantic import BaseModel, Field


class TelegramContact(BaseModel):
    phone_number: str
    first_name: str
    last_name: str | None = None
    user_id: int | None = None


class TelegramChat(BaseModel):
    id: int


class TelegramMessage(BaseModel):
    chat: TelegramChat
    text: str | None = None
    contact: TelegramContact | None = None


class TelegramUpdate(BaseModel):
    update_id: int
    message: TelegramMessage | None = Field(default=None)
