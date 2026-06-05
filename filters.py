from typing import Any
from aiogram.filters import BaseFilter
from aiogram.types import Message

import vars


class AdminFilter(BaseFilter):

    def __init__(self) -> None:
        super().__init__()

    async def __call__(self, message: Message) -> Any:
        return message.from_user.id in vars.admin_ids
