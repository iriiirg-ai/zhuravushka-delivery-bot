import asyncio
import html
import logging
import re
from typing import Dict

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove)

import db
from config import ADMIN_USERNAME, BOT_TOKEN, CAFES

logging.basicConfig(level=logging.INFO)
router = Router()


def is_admin(user) -> bool:
    return bool(user and user.username and user.username.lower() == ADMIN_USERNAME)


def main_menu(admin=False):
    rows = [[KeyboardButton(text='🛍 Сделать заказ'), KeyboardButton(text='🛒 Корзина')]]
    if admin:
        rows.append([KeyboardButton(text='⚙️ Администратор')])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def cafes_kb(prefix='cafe'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔴 PUPU', callback_data=f'{prefix}:PUPU')],
        [InlineKeyboardButton(text='🟢 Кофетюр', callback_data=f'{prefix}:Кофетюр')],
    ])


def categories_kb():
    rows = [[InlineKeyboardButton(text=c, callback_data=f'cat:{c}')] for c in db.list_categories()]
    rows.append([InlineKeyboardButton(text='🛒 Корзина', callback_data='cart:view')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def products_kb(category):
    rows = []
    for p in db.list_products(category):
        price_label = f"{p['price']} ₽" if p['price'] else "цена уточняется"
        rows.append([InlineKeyboardButton(text=f"{p['name']} · {price_label}", callback_data=f"prod:{p['id']}")])
    rows.append([InlineKeyboardButton(text='⬅️ Категории', callback_data='shop:categories')])
    rows.append([InlineKeyboardButton(text='🛒 Корзина', callback_data='cart:view')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_kb(pid, qty=1):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='➖', callback_data=f'qty:{pid}:{max(1,qty-1)}'),
         InlineKeyboardButton(text=str(qty), callback_data='noop'),
         InlineKeyboardButton(text='➕', callback_data=f'qty:{pid}:{qty+1}')],
        [InlineKeyboardButton(text='🛒 Добавить в корзину', callback_data=f'add:{pid}:{qty}')],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='shop:categories')],
    ])


def cart_text(cart: Dict[int, dict]):
    if not cart:
        return '🛒 <b>Корзина пуста</b>'
    total = 0
    lines = ['🛒 <b>Ваш заказ</b>', '']
    for item in cart.values():
        subtotal = item['price'] * item['quantity']
        total += subtotal
        if item['price']:
            price_text = f"{subtotal} ₽"
        else:
            price_text = "цена уточняется"
        lines.append(f"• <b>{html.escape(item['name'])}</b>\n  {html.escape(item['package_label'])} × {item['quantity']} = {price_text}")
    lines += ['', f'💰 <b>Итого: {total} ₽</b>']
    return '\n'.join(lines)


def cart_kb(cart):
    rows = []
    for pid, item in cart.items():
        rows.append([
            InlineKeyboardButton(text='➖', callback_data=f'cartdec:{pid}'),
            InlineKeyboardButton(text=f"{item['name']} × {item['quantity']}", callback_data='noop'),
            InlineKeyboardButton(text='➕', callback_data=f'cartinc:{pid}'),
        ])
    if cart:
        rows.append([InlineKeyboardButton(text='✅ Оформить заказ', callback_data='checkout:start')])
        rows.append([InlineKeyboardButton(text='🗑 Очистить корзину', callback_data='cart:clear')])
    rows.append([InlineKeyboardButton(text='➕ Продолжить покупки', callback_data='shop:categories')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


class ShopFlow(StatesGroup):
    cafe = State()

class Checkout(StatesGroup):
    name = State(); phone = State(); fulfillment = State(); cafe = State(); address = State(); confirm = State()

class AddProduct(StatesGroup):
    category = State(); name = State(); package = State(); price = State(); confirm = State()

class EditProduct(StatesGroup):
    choose = State(); action = State(); value = State()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(cart={})
    await message.answer('🪽 <b>Журавушка</b>\n\nДомашние полуфабрикаты, выпечка и завтраки. Соберите заказ в корзину, а мы передадим его выбранному кафе.',
                         reply_markup=main_menu(is_admin(message.from_user)))

@router.message(F.text == '🛍 Сделать заказ')
async def shop(message: Message, state: FSMContext):
    data = await state.get_data()
    if 'cart' not in data:
        await state.update_data(cart={})
    await state.set_state(ShopFlow.cafe)
    await message.answer(
        'Сначала выберите витрину, из которой будет оформлен заказ:',
        reply_markup=cafes_kb('shopcafe')
    )

@router.callback_query(ShopFlow.cafe, F.data.startswith('shopcafe:'))
async def shop_cafe_selected(c: CallbackQuery, state: FSMContext):
    cafe = c.data.split(':', 1)[1]
    await state.update_data(cafe=cafe)
    await state.set_state(None)
    await c.message.edit_text(
        f'🏪 Вы выбрали: <b>{html.escape(cafe)}</b>\n\nТеперь выберите категорию:',
        reply_markup=categories_kb()
    )
    await c.answer()

@router.callback_query(F.data == 'shop:categories')
async def cb_categories(c: CallbackQuery):
    await c.message.edit_text('Выберите категорию:', reply_markup=categories_kb()); await c.answer()

@router.callback_query(F.data.startswith('cat:'))
async def cb_cat(c: CallbackQuery):
    category = c.data.split(':',1)[1]
    await c.message.edit_text(f'📂 <b>{html.escape(category)}</b>', reply_markup=products_kb(category)); await c.answer()

@router.callback_query(F.data.startswith('prod:'))
async def cb_prod(c: CallbackQuery):
    pid = int(c.data.split(':')[1]); p = db.get_product(pid)
    if not p or not p['active']:
        await c.answer('Позиция временно недоступна', show_alert=True); return
    price_line = f"{p['price']} ₽" if p['price'] else "цена уточняется"
    text = f"<b>{html.escape(p['name'])}</b>\n⚖️ {html.escape(p['package_label'])}\n💰 {price_line}\n\nВыберите количество:"
    await c.message.edit_text(text, reply_markup=product_kb(pid,1)); await c.answer()

@router.callback_query(F.data.startswith('qty:'))
async def cb_qty(c: CallbackQuery):
    _, pid, qty = c.data.split(':'); pid=int(pid); qty=min(99,max(1,int(qty))); p=db.get_product(pid)
    price_line = f"{p['price']} ₽" if p['price'] else "цена уточняется"
    text=f"<b>{html.escape(p['name'])}</b>\n⚖️ {html.escape(p['package_label'])}\n💰 {price_line}\n\nВыберите количество:"
    await c.message.edit_reply_markup(reply_markup=product_kb(pid,qty)); await c.answer()

@router.callback_query(F.data.startswith('add:'))
async def cb_add(c: CallbackQuery, state: FSMContext):
    _, pid, qty = c.data.split(':'); pid=int(pid); qty=int(qty); p=db.get_product(pid)
    data=await state.get_data(); cart=data.get('cart',{})
    item=cart.get(pid, {'product_id':pid,'name':p['name'],'package_label':p['package_label'],'price':p['price'],'quantity':0})
    item['quantity'] += qty; cart[pid]=item; await state.update_data(cart=cart)
    await c.answer(f'Добавлено: {qty} шт.', show_alert=True)
    await c.message.edit_text(cart_text(cart), reply_markup=cart_kb(cart))

@router.message(F.text == '🛒 Корзина')
async def cart_msg(message: Message, state: FSMContext):
    cart=(await state.get_data()).get('cart',{})
    await message.answer(cart_text(cart), reply_markup=cart_kb(cart))

@router.callback_query(F.data == 'cart:view')
async def cart_view(c: CallbackQuery, state: FSMContext):
    cart=(await state.get_data()).get('cart',{})
    await c.message.edit_text(cart_text(cart), reply_markup=cart_kb(cart)); await c.answer()

@router.callback_query(F.data.startswith(('cartinc:','cartdec:')))
async def cart_change(c: CallbackQuery, state: FSMContext):
    action,pid=c.data.split(':'); pid=int(pid); data=await state.get_data(); cart=data.get('cart',{})
    if pid in cart:
        cart[pid]['quantity'] += 1 if action=='cartinc' else -1
        if cart[pid]['quantity'] <= 0: cart.pop(pid)
    await state.update_data(cart=cart)
    await c.message.edit_text(cart_text(cart), reply_markup=cart_kb(cart)); await c.answer()

@router.callback_query(F.data == 'cart:clear')
async def cart_clear(c: CallbackQuery, state: FSMContext):
    await state.update_data(cart={}); await c.message.edit_text(cart_text({}), reply_markup=cart_kb({})); await c.answer('Корзина очищена')

@router.callback_query(F.data == 'checkout:start')
async def checkout(c: CallbackQuery, state: FSMContext):
    cart=(await state.get_data()).get('cart',{})
    if not cart: await c.answer('Корзина пуста', show_alert=True); return
    await state.set_state(Checkout.name)
    await c.message.answer('Как вас зовут?', reply_markup=ReplyKeyboardRemove()); await c.answer()

@router.message(Checkout.name)
async def checkout_name(message: Message, state: FSMContext):
    name=message.text.strip()
    if len(name)<2: await message.answer('Напишите имя ещё раз.'); return
    await state.update_data(guest_name=name); await state.set_state(Checkout.phone)
    kb=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='📱 Отправить мой номер', request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)
    await message.answer('Укажите номер телефона или нажмите кнопку ниже:', reply_markup=kb)

@router.message(Checkout.phone)
async def checkout_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else (message.text or '').strip()
    digits=re.sub(r'\D','',phone)
    if len(digits)<10: await message.answer('Не удалось распознать номер. Введите его полностью.'); return
    await state.update_data(phone=phone); await state.set_state(Checkout.fulfillment)
    kb=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='🚗 Доставка'),KeyboardButton(text='🏃 Самовывоз')]], resize_keyboard=True, one_time_keyboard=True)
    await message.answer('Как вы хотите получить заказ?', reply_markup=kb)

@router.message(Checkout.fulfillment, F.text.in_({'🚗 Доставка','🏃 Самовывоз'}))
async def fulfillment(message: Message, state: FSMContext):
    value='delivery' if 'Доставка' in message.text else 'pickup'
    await state.update_data(fulfillment=value)
    data = await state.get_data()
    selected_cafe = data.get('cafe')
    if selected_cafe:
        if value == 'delivery':
            await state.set_state(Checkout.address)
            await message.answer(
                f'Заказ оформляется из витрины <b>{html.escape(selected_cafe)}</b>.\nВведите адрес доставки:',
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await state.update_data(address=None)
            await show_confirm(message, state)
    else:
        await state.set_state(Checkout.cafe)
        await message.answer('Выберите кафе, которое будет готовить заказ:', reply_markup=ReplyKeyboardRemove())
        await message.answer('🔴 PUPU или 🟢 Кофетюр', reply_markup=cafes_kb('checkoutcafe'))

@router.callback_query(Checkout.cafe, F.data.startswith('checkoutcafe:'))
async def checkout_cafe(c: CallbackQuery, state: FSMContext):
    cafe=c.data.split(':',1)[1]; await state.update_data(cafe=cafe)
    data=await state.get_data()
    if data['fulfillment']=='delivery':
        await state.set_state(Checkout.address); await c.message.answer('Введите адрес доставки:'); await c.answer()
    else:
        await state.update_data(address=None); await show_confirm(c.message,state); await c.answer()

@router.message(Checkout.address)
async def address(message: Message, state: FSMContext):
    if len(message.text.strip())<5: await message.answer('Введите адрес подробнее.'); return
    await state.update_data(address=message.text.strip()); await show_confirm(message,state)

async def show_confirm(message: Message, state: FSMContext):
    data=await state.get_data(); cart=data['cart']; cafe=data['cafe']; f=data['fulfillment']
    text=[cart_text(cart),'',f"👤 {html.escape(data['guest_name'])}",f"📞 {html.escape(data['phone'])}",f"🏪 <b>{cafe}</b>",f"📦 {'Доставка' if f=='delivery' else 'Самовывоз'}"]
    if data.get('address'): text.append(f"📍 {html.escape(data['address'])}")
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='✅ Подтвердить заказ', callback_data='checkout:confirm')],[InlineKeyboardButton(text='❌ Отменить', callback_data='checkout:cancel')]])
    await state.set_state(Checkout.confirm); await message.answer('\n'.join(text), reply_markup=kb)

@router.callback_query(Checkout.confirm, F.data == 'checkout:cancel')
async def cancel_checkout(c: CallbackQuery, state: FSMContext):
    await state.clear(); await state.update_data(cart={}); await c.message.answer('Заказ отменён.', reply_markup=main_menu(is_admin(c.from_user))); await c.answer()


def order_chat_text(order, items):
    cafe=order['cafe']; meta=CAFES[cafe]; delivery=order['fulfillment']=='delivery'
    header=f"{meta['emoji']*3} <b>НОВЫЙ ЗАКАЗ {html.escape(cafe.upper())} №{order['id']:04d}</b> {meta['emoji']*3}"
    lines=[header,'',f"👤 <b>Имя:</b> {html.escape(order['guest_name'])}",f"📞 <b>Телефон:</b> {html.escape(order['phone'])}",f"📦 <b>Получение:</b> {'🚗 Доставка' if delivery else '🏃 Самовывоз'}"]
    if delivery: lines.append(f"📍 <b>Адрес:</b> {html.escape(order['address'] or '')}")
    else: lines.append(f"🏪 <b>Самовывоз:</b> {html.escape(cafe)} · {meta['phone']}")
    lines += ['', '🛒 <b>Состав заказа:</b>']
    for i in items:
        price_text = f"{i['price']*i['quantity']} ₽" if i['price'] else "цена уточняется"
        lines.append(f"• {html.escape(i['product_name'])}\n  {html.escape(i['package_label'])} × {i['quantity']} = {price_text}")
    unknown_prices = any(not i['price'] for i in items)
    total_line = f"💰 <b>Итого по товарам с указанной ценой: {order['total']} ₽</b>" if unknown_prices else f"💰 <b>Итого: {order['total']} ₽</b>"
    lines += ['', total_line]
    if unknown_prices:
        lines.append('ℹ️ Стоимость позиций без цены сотрудник уточнит при подтверждении заказа.')
    lines += ['', '⏳ Статус: новый заказ']
    return '\n'.join(lines)


def status_kb(order_id, fulfillment, status='new'):
    rows=[]
    if status=='new': rows=[[InlineKeyboardButton(text='✅ Принять заказ', callback_data=f'status:{order_id}:accepted')]]
    elif status=='accepted': rows=[[InlineKeyboardButton(text='👨‍🍳 Готовится', callback_data=f'status:{order_id}:cooking')]]
    elif status=='cooking': rows=[[InlineKeyboardButton(text='📦 Заказ готов', callback_data=f'status:{order_id}:ready')]]
    elif status=='ready':
        label='🚗 Передан курьеру' if fulfillment=='delivery' else '✅ Выдан гостю'
        next_status='courier' if fulfillment=='delivery' else 'completed'
        rows=[[InlineKeyboardButton(text=label, callback_data=f'status:{order_id}:{next_status}')]]
    elif status=='courier': rows=[[InlineKeyboardButton(text='✅ Доставлен', callback_data=f'status:{order_id}:completed')]]
    if status not in {'completed','cancelled'}:
        rows.append([InlineKeyboardButton(text='❌ Отменить заказ', callback_data=f'status:{order_id}:cancelled')])
    return InlineKeyboardMarkup(inline_keyboard=rows)

@router.callback_query(Checkout.confirm, F.data == 'checkout:confirm')
async def confirm_order(c: CallbackQuery, state: FSMContext, bot: Bot):
    data=await state.get_data(); cart=list(data['cart'].values())
    oid=db.create_order(c.from_user.id,data['guest_name'],data['phone'],data['fulfillment'],data['cafe'],data.get('address'),cart)
    order,items=db.get_order(oid); chat_id=db.get_setting('orders_chat_id')
    if not chat_id:
        await c.message.answer('Заказ сохранён, но рабочий чат ещё не подключён. Позвоните в кафе для подтверждения.'); await c.answer(); return
    try:
        sent=await bot.send_message(int(chat_id),order_chat_text(order,items),reply_markup=status_kb(oid,order['fulfillment']))
        db.update_order(oid,work_chat_message_id=sent.message_id)
        meta=CAFES[order['cafe']]
        await c.message.answer(f"✅ <b>Заказ №{oid:04d} оформлен!</b>\n\nКафе: <b>{order['cafe']}</b>\nТелефон: {meta['phone']}\nМы будем присылать сюда изменения статуса.", reply_markup=main_menu(is_admin(c.from_user)))
        await state.clear(); await state.update_data(cart={})
    except Exception as e:
        logging.exception('Failed to send order')
        await c.message.answer('Заказ сохранён, но сообщение не удалось отправить в рабочий чат. Позвоните в кафе для подтверждения.')
    await c.answer()

STATUS_LABELS={'accepted':'✅ Заказ принят','cooking':'👨‍🍳 Заказ готовится','ready':'📦 Заказ готов','courier':'🚗 Передан курьеру','completed':'✅ Заказ завершён','cancelled':'❌ Заказ отменён'}

@router.callback_query(F.data.startswith('status:'))
async def change_status(c: CallbackQuery, bot: Bot):
    _,oid_s,status=c.data.split(':'); oid=int(oid_s); order,items=db.get_order(oid)
    if not order: await c.answer('Заказ не найден',show_alert=True); return
    staff=c.from_user.full_name
    db.update_order(oid,status=status,staff_name=staff)
    order,items=db.get_order(oid)
    text=order_chat_text(order,items).rsplit('⏳ Статус:',1)[0] + f"{STATUS_LABELS[status]}\n👤 Изменил: {html.escape(staff)}"
    try: await c.message.edit_text(text,reply_markup=status_kb(oid,order['fulfillment'],status))
    except TelegramBadRequest: pass
    guest_msgs={
      'accepted':f'✅ Ваш заказ №{oid:04d} принят кафе {order["cafe"]}.',
      'cooking':f'👨‍🍳 Ваш заказ №{oid:04d} уже готовится.',
      'ready':f'📦 Ваш заказ №{oid:04d} готов.' + (f' Самовывоз из {order["cafe"]}. Телефон: {CAFES[order["cafe"]]["phone"]}.' if order['fulfillment']=='pickup' else ''),
      'courier':f'🚗 Ваш заказ №{oid:04d} передан курьеру.',
      'completed':f'✅ Заказ №{oid:04d} завершён. Спасибо за заказ!',
      'cancelled':f'❌ Заказ №{oid:04d} отменён. Для уточнения позвоните: {CAFES[order["cafe"]]["phone"]}.',
    }
    try: await bot.send_message(order['guest_tg_id'],guest_msgs[status])
    except Exception: logging.exception('Guest notification failed')
    await c.answer(STATUS_LABELS[status])

@router.message(Command('connect_orders'))
async def connect_orders(message: Message):
    if message.chat.type=='private': await message.answer('Команду нужно отправить в рабочем групповом чате.'); return
    if not is_admin(message.from_user): await message.answer('Подключить чат может только администратор.'); return
    db.set_setting('orders_chat_id',str(message.chat.id)); await message.answer('✅ Этот чат подключён для заказов.')

@router.message(Command('test_order_chat'))
async def test_order_chat(message: Message):
    if not is_admin(message.from_user): return
    chat_id=db.get_setting('orders_chat_id')
    if not chat_id: await message.answer('Сначала отправьте /connect_orders в рабочем чате.'); return
    await message.bot.send_message(int(chat_id),'✅ Тест успешен: бот может присылать сюда заказы.')

# ADMIN
@router.message(F.text == '⚙️ Администратор')
async def admin_menu(message: Message):
    if not is_admin(message.from_user): return
    kb=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='➕ Добавить позицию'),KeyboardButton(text='📋 Управление товарами')],[KeyboardButton(text='🏠 Главное меню')]],resize_keyboard=True)
    await message.answer('⚙️ <b>Администратор</b>',reply_markup=kb)

@router.message(F.text == '🏠 Главное меню')
async def home(message: Message,state:FSMContext):
    await state.clear(); await state.update_data(cart={}); await message.answer('Главное меню',reply_markup=main_menu(is_admin(message.from_user)))

@router.message(F.text == '➕ Добавить позицию')
async def ap_start(message:Message,state:FSMContext):
    if not is_admin(message.from_user): return
    await state.set_state(AddProduct.category); await message.answer('Введите категорию товара:',reply_markup=ReplyKeyboardRemove())

@router.message(AddProduct.category)
async def ap_cat(message:Message,state:FSMContext):
    await state.update_data(ap_category=message.text.strip()); await state.set_state(AddProduct.name); await message.answer('Введите название:')
@router.message(AddProduct.name)
async def ap_name(message:Message,state:FSMContext):
    await state.update_data(ap_name=message.text.strip()); await state.set_state(AddProduct.package); await message.answer('Введите вес или фасовку, например «450 г» или «3 шт., 350 г»:')
@router.message(AddProduct.package)
async def ap_pack(message:Message,state:FSMContext):
    await state.update_data(ap_package=message.text.strip()); await state.set_state(AddProduct.price); await message.answer('Введите цену в рублях, только число:')
@router.message(AddProduct.price)
async def ap_price(message:Message,state:FSMContext):
    if not message.text.isdigit() or int(message.text)<=0: await message.answer('Введите цену целым числом.'); return
    await state.update_data(ap_price=int(message.text)); data=await state.get_data(); await state.set_state(AddProduct.confirm)
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='✅ Добавить',callback_data='ap:confirm')],[InlineKeyboardButton(text='❌ Отмена',callback_data='ap:cancel')]])
    await message.answer(f"Добавить товар?\n\nКатегория: {html.escape(data['ap_category'])}\nНазвание: {html.escape(data['ap_name'])}\nФасовка: {html.escape(data['ap_package'])}\nЦена: {data['ap_price']} ₽",reply_markup=kb)
@router.callback_query(AddProduct.confirm,F.data=='ap:confirm')
async def ap_confirm(c:CallbackQuery,state:FSMContext):
    data=await state.get_data()
    try: db.add_product(data['ap_category'],data['ap_name'],data['ap_package'],data['ap_price'],1); text='✅ Позиция добавлена и доступна гостям.'
    except Exception: text='Не удалось добавить. Возможно, такое название уже существует.'
    await state.clear(); await c.message.answer(text,reply_markup=main_menu(True)); await c.answer()
@router.callback_query(AddProduct.confirm,F.data=='ap:cancel')
async def ap_cancel(c:CallbackQuery,state:FSMContext):
    await state.clear(); await c.message.answer('Добавление отменено.',reply_markup=main_menu(True)); await c.answer()

@router.message(F.text == '📋 Управление товарами')
async def manage(message:Message):
    if not is_admin(message.from_user): return
    rows=[]
    for p in db.list_products(active_only=False):
        mark='✅' if p['active'] else '⏸'; price=f"{p['price']} ₽" if p['price'] else 'цена не задана'
        rows.append([InlineKeyboardButton(text=f"{mark} {p['name']} · {price}",callback_data=f'manage:{p["id"]}')])
    await message.answer('Выберите товар:',reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@router.callback_query(F.data.startswith('manage:'))
async def manage_product(c:CallbackQuery):
    if not is_admin(c.from_user): return
    pid=int(c.data.split(':')[1]); p=db.get_product(pid)
    kb=InlineKeyboardMarkup(inline_keyboard=[
      [InlineKeyboardButton(text='💰 Изменить цену',callback_data=f'editprice:{pid}')],
      [InlineKeyboardButton(text='⚖️ Изменить вес/фасовку',callback_data=f'editpack:{pid}')],
      [InlineKeyboardButton(text='⏸ Скрыть' if p['active'] else '✅ Показать',callback_data=f'toggle:{pid}')],
    ])
    await c.message.answer(f"<b>{html.escape(p['name'])}</b>\n{html.escape(p['package_label'])}\nЦена: {p['price'] or 'не задана'}",reply_markup=kb); await c.answer()

@router.callback_query(F.data.startswith('toggle:'))
async def toggle(c:CallbackQuery):
    pid=int(c.data.split(':')[1]); p=db.get_product(pid); db.update_product(pid,active=0 if p['active'] else 1); await c.answer('Готово',show_alert=True)

@router.callback_query(F.data.startswith(('editprice:','editpack:')))
async def edit_start(c:CallbackQuery,state:FSMContext):
    action,pid=c.data.split(':'); await state.update_data(edit_pid=int(pid),edit_action=action); await state.set_state(EditProduct.value)
    await c.message.answer('Введите новую цену, только число:' if action=='editprice' else 'Введите новый вес или фасовку:'); await c.answer()

@router.message(EditProduct.value)
async def edit_value(message:Message,state:FSMContext):
    data=await state.get_data(); pid=data['edit_pid']; action=data['edit_action']
    if action=='editprice':
        if not message.text.isdigit() or int(message.text)<=0: await message.answer('Введите целое число.'); return
        db.update_product(pid,price=int(message.text),active=1)
    else: db.update_product(pid,package_label=message.text.strip())
    await state.clear(); await message.answer('✅ Изменения сохранены.',reply_markup=main_menu(True))

@router.callback_query(F.data=='noop')
async def noop(c:CallbackQuery): await c.answer()

async def main():
    if not BOT_TOKEN: raise RuntimeError('BOT_TOKEN is not set')
    db.init_db()
    bot = Bot(
        BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp=Dispatcher(storage=MemoryStorage()); dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot)

if __name__=='__main__': asyncio.run(main())
