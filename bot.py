import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN ="9163706619:AAExD0BGXZFB_9EFkJ8HBTpG6u7t2azmqK0"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Состояния для регистрации ---
class Reg(StatesGroup):
    logo = State()
    team_name = State()
    captain = State()
    players = State()  # будем собирать по одному

# --- Клавиатура главного меню ---
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Регистрация")],
        [KeyboardButton(text="Пример заявки")],
        [KeyboardButton(text="Правила по заявке")],
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Это бот для регистрации на турнир **Destour**. С чем могу вам помочь?",
        reply_markup=main_kb,
        parse_mode="Markdown"
    )

# --- Пример заявки ---
@dp.message(F.text == "Пример заявки")
async def example(message: types.Message):
    text = (
        "📋 **Пример заявки команды на турнир:**\n\n"
        "Логотип: (пришлите фото или ссылку)\n"
        "Название команды: ____\n"
        "Средний MMR: _____\n"
        "Капитан команды: _____\n"
        "Состав команды:\n"
        "Основной\n"
        "1) Фамилия Имя | Никнейм | Позиция | MMR\n"
        "2) ...\n"
        "3) ...\n"
        "4) ...\n"
        "5) ...\n"
        "Запасные\n"
        "6) ...\n"
        "7) ...\n"
        "8) ...\n\n"
        "⚠️ Ограничение: сумма MMR команды не более **20000**."
    )
    await message.answer(text, parse_mode="Markdown")

# --- Правила по заявке ---
@dp.message(F.text == "Правила по заявке")
async def rules(message: types.Message):
    text = (
        "📜 **Правила по заявке:**\n"
        "1. В заявке указываются: логотип, название команды, средний MMR, капитан.\n"
        "2. Состав: 5 основных + до 3 запасных.\n"
        "3. У каждого участника: Фамилия Имя, Никнейм, Позиция, MMR.\n"
        "4. Суммарный MMR команды (основной состав) не должен превышать **20000**.\n"
        "5. Заявка отправляется через кнопку «Регистрация»."
    )
    await message.answer(text, parse_mode="Markdown")

# --- Регистрация ---
@dp.message(F.text == "Регистрация")
async def reg_start(message: types.Message, state: FSMContext):
    await state.set_state(Reg.logo)
    await message.answer("Шаг 1. Пришлите логотип команды (фото или ссылку).")

@dp.message(Reg.logo)
async def reg_logo(message: types.Message, state: FSMContext):
    await state.update_data(logo=message.text or "фото")
    await state.set_state(Reg.team_name)
    await message.answer("Шаг 2. Название команды:")

@dp.message(Reg.team_name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(team_name=message.text)
    await state.set_state(Reg.captain)
    await message.answer("Шаг 3. Капитан команды (Фамилия Имя | Никнейм | MMR):")

@dp.message(Reg.captain)
async def reg_captain(message: types.Message, state: FSMContext):
    await state.update_data(captain=message.text, players=[])
    await state.set_state(Reg.players)
    await message.answer(
        "Шаг 4. Введите игроков по одному в формате:\n"
        "`Фамилия Имя | Никнейм | Позиция | MMR`\n\n"
        "Сначала 5 основных, потом запасных (до 3).\n"
        "Когда закончите — напишите **готово**.",
        parse_mode="Markdown"
    )

@dp.message(Reg.players, F.text.lower() == "готово")
async def reg_done(message: types.Message, state: FSMContext):
    data = await state.get_data()
    players = data.get("players", [])
    if len(players) < 5:
        await message.answer("Нужно минимум 5 основных игроков. Продолжайте.")
        return

    # Считаем сумму MMR
    total_mmr = 0
    for p in players:
        try:
            total_mmr += int(p.split("|")[-1].strip())
        except:
            pass

    if total_mmr > 20000:
        await message.answer(f"❌ Сумма MMR = {total_mmr}, это больше лимита 20000. Заявка отклонена.")
        await state.clear()
        return

    text = (
        f"✅ **Заявка принята**\n"
        f"Логотип: {data['logo']}\n"
        f"Название: {data['team_name']}\n"
        f"Капитан: {data['captain']}\n"
        f"Состав:\n" + "\n".join(players) +
        f"\n\nСумма MMR: {total_mmr} (лимит 20000)"
    )
    await message.answer(text, parse_mode="Markdown")
    await state.clear()

@dp.message(Reg.players)
async def reg_player(message: types.Message, state: FSMContext):
    data = await state.get_data()
    players = data.get("players", [])
    players.append(message.text)
    await state.update_data(players=players)
    await message.answer(f"Игрок добавлен ({len(players)}). Введите следующего или напишите **готово**.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
