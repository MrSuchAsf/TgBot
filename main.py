import logging
import threading

logging.basicConfig(level=logging.DEBUG)

from FunPayCardinal.FunPayAPI import Account, Runner
from FunPayCardinal.FunPayAPI.updater.events import NewMessageEvent
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
        print("================================")
        print("Text: ", msg.text)
        print("Autor: ",msg.author)
        print("Vse polya: ",vars(msg))
        print("================================")

        try:
            print("Заказ: ",msg._order)
            print("Название заказа: ",vars(msg._order) if msg._order else "Нету заказа")
        except Exception as e:
            print("Ошибка при получении заказа", e)