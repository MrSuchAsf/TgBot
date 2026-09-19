import logging
import threading
import re

logging.basicConfig(level=logging.DEBUG)

from FunPayCardinal.FunPayAPI import Account, Runner
from FunPayCardinal.FunPayAPI.updater.events import NewMessageEvent
from FunPayCardinal.FunPayAPI.common.enums import MessageTypes
from FunPayCardinal.FunPayAPI.types import Order
from config import GOLDEN_KEY

acc = Account(GOLDEN_KEY).get() #type: ignore

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

runner = Runner(acc)
# Запускаем фоновый поток, который реально обрабатывает очередь запросов
threading.Thread(target=runner.loop, daemon=True).start()

for event in runner.listen(requests_delay=4):
    if isinstance(event, NewMessageEvent):
        msg = event.message

        if msg.type == MessageTypes.ORDER_PURCHASED and msg.text:
            match = re.search(r"#([A-Z0-9]+)", msg.text)
            if match:
                order_id = match.group(1)
                print("Number of order: ", order_id)

                order = acc.get_order(order_id)
                
                print("Value: ", vars(order))
                print("Subcategory: ", vars(order.subcategory))
                print("--------------------------")
                for key, field in order.fields.items():
                    print(f"Field: {key}: ", vars(field))

                wynik = fp_order(order)
                print("Order: ", wynik)
                



    
