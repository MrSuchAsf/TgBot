import logging
import threading
import re

logging.basicConfig(level=logging.DEBUG)

from FunPayCardinal.FunPayAPI import Account, Runner
from FunPayCardinal.FunPayAPI.updater.events import NewMessageEvent
from FunPayCardinal.FunPayAPI.common.enums import MessageTypes
from config import GOLDEN_KEY

acc = Account(GOLDEN_KEY).get() #type: ignore
print(f"✅ Вошли в FunPay: {acc.username}")

runner = Runner(acc)
# Запускаем фоновый поток, который реально обрабатывает очередь запросов
threading.Thread(target=runner.loop, daemon=True).start()

print("🚀 Runner запущен. Жду события...")

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
            