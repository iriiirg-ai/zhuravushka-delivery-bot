# Журавушка Delivery Bot

Telegram-бот заказов для PUPU и Кофетюра.

## Railway Variables

- `BOT_TOKEN` — токен нового бота `@zhuravushka_delivery_bot`
- `ADMIN_USERNAME` — `inminlu`
- `DATABASE_PATH` — `/data/zhuravushka_delivery.db`
- `TIMEZONE` — `Asia/Yakutsk`

Подключите Railway Volume к `/data`.

## Подключение рабочего чата

Добавьте бота администратором в рабочий чат и отправьте от `@inminlu`:

`/connect_orders`

Проверка:

`/test_order_chat`

## Важно про цены

Позиции с известной ценой сразу активны. Позиции без подтверждённой цены скрыты от гостей. Администратор задаёт им цену через `⚙️ Администратор → 📋 Управление товарами`, после чего товар автоматически становится доступным.
