from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format, List
from aiogram_dialog.widgets.kbd import (
    NextPage, PrevPage, LastPage, FirstPage, CurrentPage, Row, Select, Button, SwitchTo, Column
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.input import TextInput

from . import controllers
from .states import RequestsStates


requests_window = Window(
    Const('Заявки'),
    DynamicMedia(
        selector='photo'
    ),
    List(
        field=Format('{item[user_text]}'),
        id='requests_list',
        items='requests',
        page_size=1,
    ),
    Select(
        text=Format('{item[0]}'),
        id='choose_select',
        item_id_getter=lambda i: i[1],
        items=[('Одобрить', 'approved'), ('Отказать', 'declined')],
        on_click=controllers.request_action,
        when='requests'
    ),
    Row(
        FirstPage(scroll='requests_list', text=Format('⏮️ {target_page1}')),
        PrevPage(scroll='requests_list', text=Const('◀️')),
        CurrentPage(scroll='requests_list', text=Format('{current_page1}')),
        NextPage(scroll='requests_list', text=Const('▶️')),
        LastPage(scroll='requests_list', text=Format('{target_page1} ⏭️'))
    ),
    Button(
        text=Const('В главное меню'), 
        id='back_btn', 
        on_click=controllers.back_to_main
    ),
    state=RequestsStates.main,
    getter=controllers.requests_getter
    )


reject_reason_window = Window(
    Const('Введите причину отказа'),
    TextInput(
        id='reject_reason_input',
        on_success=controllers.reject_reason_success
    ),
    Column(
        SwitchTo(
            text=Const('Пропустить'),
            id='skip_btn',
            state=RequestsStates.main
        ),
        Button(
            text=Const('В главное меню'), 
            id='back_btn', 
            on_click=controllers.back_to_main
        )
    ),
    state=RequestsStates.reject_reason
)
