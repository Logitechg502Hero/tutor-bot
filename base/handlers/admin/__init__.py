from aiogram import Router

from .connect import router as connect_router
from .base import router as base_router
from .find_user import router as find_user_router
from .requests_dialogs import requests_dialog


router = Router()

router.include_router(connect_router)
router.include_router(base_router)
router.include_router(find_user_router)
router.include_router(requests_dialog)
