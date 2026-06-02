from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import ManagedRadio, Button
from aiogram_dialog.widgets.text import List
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from aiogram.types import CallbackQuery
from aiogram.enums.content_type import ContentType

from .states import RequestsStates

from datetime import datetime

from utils import user_text as util_user_text

from base.visual.markups import admin as admin_markups
from base.visual.texts import user as user_texts

import shutil
import constants

import vars


async def requests_getter(dialog_manager: DialogManager, **kwargs):
    requests = vars.database.get_requests_by_status(statuses=['pending'])
    requests_scroll: List = dialog_manager.find('requests_list')
    current_page = await requests_scroll.get_page()
    requests_list = list()
    for request in requests:
        _data = util_user_text.resolve_user_data(request['user_id'])
        requests_list.append({
            'user_text': _data[0] + f'\n\nUser ID: {request["user_id"]}',
            'photo_path': _data[1],
            'user_id': request['user_id']
        })
    if not requests_list:
        return {
            'requests': [],
            'photo': None
        }
    data = {
        'requests': requests_list,
        'photo': None if requests_list[current_page]['photo_path'] is None else MediaAttachment(
            type=ContentType.PHOTO,
            path=requests_list[current_page]['photo_path']
        )
    }
    dialog_manager.dialog_data['requests'] = requests_list
    return data


async def request_action(callback: CallbackQuery, radio: ManagedRadio, dialog_manager: DialogManager, status: str):
    current_page = await dialog_manager.find('requests_list').get_page()
    user_id = dialog_manager.dialog_data['requests'][current_page]['user_id']
    user = vars.database.get_user(user_id)
    if not user:
        return
    if status == 'approved':
        vars.database.upsert_request(user_id, datetime.now(), 'approved')
    elif status == 'declined':
        vars.database.upsert_request(user_id, datetime.now(), 'rejected')
        await dialog_manager.switch_to(RequestsStates.reject_reason)


async def back_to_main(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):

    await dialog_manager.done()
    await callback.message.answer('Выберите действие', reply_markup=admin_markups.main_kb)


async def reject_reason_success(callback: CallbackQuery, input: TextInput, dialog_manager: DialogManager, reason: str):

    current_page = await dialog_manager.find('requests_list').get_page()
    user_id = dialog_manager.dialog_data['requests'][current_page]['user_id']
    user = vars.database.get_user(user_id)
    if not user:
        await dialog_manager.switch_to(RequestsStates.main)
    await vars.bot.send_message(user_id, user_texts.request_rejected_text.format(reason=reason))
    await dialog_manager.switch_to(RequestsStates.main)
