import logging
import threading
import re

logging.basicConfig(level=logging.DEBUG)

from database import init_db, create_order
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import BOT_TOKEN, MY_ID_TELEGRAM
import asyncio
from FunPayCardinal.FunPayAPI import Account, Runner
from FunPayCardinal.FunPayAPI.updater.events import NewMessageEvent
from FunPayCardinal.FunPayAPI.common.enums import MessageTypes
from FunPayCardinal.FunPayAPI.types import Order
from config import GOLDEN_KEY

acc = Account(GOLDEN_KEY).get() #type: ignore
bot = Bot(token=BOT_TOKEN) #type: ignore

CATEGORY_MAP = {
    "Сеты": "sets",
    "Сопровождение": "sopr",
    "Буст баланса": "bust",
}

def fp_order(order: Order) -> tuple[str, str, int] | None:
    type_field = order.fields.get("type")
    summary_field = order.fields.get("summary")

    if not type_field or not summary_field:
        return None

    if not isinstance(type_field.value, str):
        return None
    category = CATEGORY_MAP.get(type_field.value)
    if category is None:
        return None

    if not isinstance(summary_field.value, dict):
        return None
    product = summary_field.value.get("ru", "None Lol")

    amount = order.amount
    return category, product, amount

pending_orders: dict[int | str, tuple[str,str,int,int]] = {}

runner = Runner(acc)
# Запускаем фоновый поток, который реально обрабатывает очередь запросов
threading.Thread(target=runner.loop, daemon=True).start()

for event in runner.listen(requests_delay=4):
    if isinstance(event, NewMessageEvent):
        msg = event.message
        if not msg.text:
            continue

        if msg.type == MessageTypes.ORDER_PURCHASED and msg.text:
            match = re.search(r"#([A-Z0-9]+)", msg.text)
            if match:
                order = acc.get_order(match.group(1))
                parsed = fp_order(order)
                if parsed:
                    category, product, amount = parsed
                    pending_orders[msg.chat_id] = (category,product,amount,order.buyer_id)

        elif msg.type == MessageTypes.NON_SYSTEM and msg.chat_id in pending_orders:
            category, product, amount, buyer_id = pending_orders[msg.chat_id]

            if msg.author_id != buyer_id:
                continue 

            pubg_id = msg.text.strip()
            if pubg_id.isdigit() and 7 <= len(pubg_id) <= 10:
                pending_orders.pop(msg.chat_id)

                order_id = create_order(pubg_id=pubg_id, product=product, amount=amount, category=category)

                keyboard_take = InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="В работу", callback_data=f"take_order_{order_id}")]]
                )

                text = (
                    f"Новая заявка №{order_id} (с FunPay)\n"
                    f"PUBG ID: {pubg_id}\n"
                    f"Тип: {product}\n"
                    f"Количество: {amount}\n"
                    f"Статус: Свободен"
                )

                asyncio.run(bot.send_message(chat_id=MY_ID_TELEGRAM, text=text, reply_markup=keyboard_take)) #type: ignore
                print(f"✅ Заказ #{order_id} создан и отправлен работягам")
                



    
