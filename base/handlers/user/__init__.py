from aiogram import Router

from .base import router as base_router
from .input_tutor import router as input_router
from .input_tutee import router as input_tutee_router
from .profile import router as profile_router
from .change import router as change_router
from .reviews import router as reviews_router

router = Router()

router.include_router(base_router)
router.include_router(input_router)
router.include_router(input_tutee_router)
router.include_router(profile_router)
router.include_router(change_router)
router.include_router(reviews_router)
