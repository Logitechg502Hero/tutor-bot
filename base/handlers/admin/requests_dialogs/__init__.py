from aiogram_dialog import Dialog

from .windows import requests_window, reject_reason_window


requests_dialog = Dialog(
    requests_window,
    reject_reason_window
)
