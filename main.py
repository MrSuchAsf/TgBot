import logging 
import threading
import re
import asyncio

logging.basicConfig(level=logging.DEBUG)

from database import init_db, create_order, get_order_by_id, update_order_status
from aiogram import Bot, F, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from config import BOT_TOKEN, MY_ID_TELEGRAM, GOLDEN_KEY
from FunPayCardinal.FunPayAPI import Account, Runner
from FunPayCardinal.FunPayAPI.updater.events import NewMessageEvent
from FunPayCardinal.FunPayAPI.common.enums import MessageTypes
from FunPayCardinal.FunPayAPI.types import Order

main_loop: asyncio.AbstractEventLoop
acc = Account(GOLDEN_KEY).get() #type: ignore
bot = Bot(token=BOT_TOKEN) #type: ignore
dp = Dispatcher()
init_db()

CATEGORY_MAP = {
    "Предметы": "sets",
    "Сопровождение": "sopr",
    "Услуги": "bust",
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

def funpay_listener():
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
                    type_field = order.fields.get("type")
                    if parsed:
                        print(repr(type_field.value if type_field else None))
                        category, product, amount = parsed

                        if category == "bust":
                            try:
                                acc.send_message(
                                    msg.chat_id,
                                    "Дождитесь меня и оставьте здесь свои пожелания по бусту."
                                )

                                text = (
                                    f"Новая заявка (буст, с FunPay)\n"
                                    f"Тип: {product}\n"
                                    f"Количество: {amount}\n"
                                    f"Покупатель: {order.buyer_username}\n"
                                    "@splod Новое задание :))"
                                )

                                order_id = create_order(pubg_id="— ", product=product, amount=amount, category=category)
                                keyboard_complete = InlineKeyboardMarkup(
                                    inline_keyboard=[[InlineKeyboardButton(text="Сделано", callback_data=f"complete_order_{order_id}")]]
                                )

                                asyncio.run_coroutine_threadsafe(bot.send_message(chat_id=MY_ID_TELEGRAM,text=text, reply_markup=keyboard_complete), main_loop)
                                print(f"Уведомление о бусте отправлено в Telegram, чат с пользователем: {msg.chat_id}")
                            except Exception as e:
                                print(f" Не удалось отправить сообщение: {e}")
                        else:
                            pending_orders[msg.chat_id] = (category, product, amount, order.buyer_id)
                            try:
                                acc.send_message(msg.chat_id, "Оставьте айди на который должен поступить товар")
                                print(f"Запросил айди в чате {msg.chat_id}")
                            except Exception as e:
                                print(f"Не удалось отправить сообщение: {e}")

            elif msg.type == MessageTypes.NON_SYSTEM and msg.chat_id in pending_orders:
                category, product, amount, buyer_id = pending_orders[msg.chat_id]

                if msg.author_id != buyer_id:
                    continue 

                pubg_id = msg.text.strip()
                if pubg_id.isdigit() and 7 <= len(pubg_id) <= 10:
                    pending_orders.pop(msg.chat_id)
                    order_id = create_order(pubg_id=pubg_id, product=product, amount=amount, category=category)

                    keyboard_complete = InlineKeyboardMarkup(
                        inline_keyboard=[[InlineKeyboardButton(text="Сделано", callback_data=f"complete_order_{order_id}")]]
                    )

                    text = (
                        f"Новая заявка №{order_id} (с FunPay)\n"
                        f"PUBG ID: {pubg_id}\n"
                        f"Тип: {product}\n"
                        f"Количество: {amount}\n"
                        f"Статус: Свободен"
                    )
                        
                    asyncio.run_coroutine_threadsafe(bot.send_message(chat_id=MY_ID_TELEGRAM,text=text, reply_markup=keyboard_complete), main_loop)
                    print(f"Заказ #{order_id} создан и отправлен работягам")
                else:
                    acc.send_message(msg.chat_id ,"Введите пожалуйста само айди.")

@dp.callback_query(F.data.startswith("complete_order_"))
async def complete_order(callback: CallbackQuery):
    if not callback.data or not callback.message:
        return

    order_id = int(callback.data.split("_")[2])

    order = get_order_by_id(order_id)
    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return

    pubg_id, product, amount, category ,status = order

    update_order_status(order_id=order_id, status="COMPLETE")

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=(
                f"Заказ {order_id} - СДЕЛАНО\n"
                f"Айди заказчика: {pubg_id}\n"
                f"Тип: {product}\n"
                f"Количество: {amount}"
            ),
            reply_markup=None,
        )

    await callback.answer(f"Заказ {order_id} закрыт")

async def main():
    global main_loop
    main_loop = asyncio.get_running_loop()
    threading.Thread(target=runner.loop, daemon=True).start()
    threading.Thread(target=funpay_listener, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
