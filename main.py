import os
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode, InputMediaPhoto
from aiogram.utils import executor
from dotenv import load_dotenv

# Memuat variabel lingkungan
load_dotenv()

# Inisialisasi bot dan dispatcher
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Tipe kartu Yu-Gi-Oh
CARD_TYPES = {
    "SPELL": "Spell Card",
    "TRAP": "Trap Card",
    "MONSTER": "Monster Card"
}

# Pesan welcome
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer(
        "*Welcome!*\n\nI can search _YU-GI-OH!_ cards for you! \n\nSend /help for more information!",
        parse_mode=ParseMode.MARKDOWN
    )

# Daftar perintah
@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await message.answer(
        "List of Commands \n\n/start - Welcome message\n/about - Credits and Bot information\n/card {card name} - Replies with a picture of the card.\n/stats {card name} - Replies with information about the card.\n/price {card name} - Replies with the current lowest price on TCGPlayer.\n/artworks {card name} - Replies with all the artworks for a given card\n/draw - Replies with a random card\n\nAll card names need to be the exact name of the card.",
        parse_mode=ParseMode.MARKDOWN
    )

# Tentang bot
@dp.message_handler(commands=['about'])
async def about(message: types.Message):
    await message.answer(
        "*Made by @delctrl*\n\nThe *Yu-gi-oh! API* can be found at https://db.ygoprodeck.com/api-guide/",
        parse_mode=ParseMode.MARKDOWN
    )

# Penanganan kesalahan
async def handle_error(message: types.Message):
    await message.reply("Card not found")

# Fungsi untuk mendapatkan informasi kartu
def get_card_data(card_name: str):
    response = requests.get(f'https://db.ygoprodeck.com/api/v7/cardinfo.php?name={card_name}')
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict) and 'data' in data and len(data['data']) > 0:
            return data['data'][0]  # Mengembalikan kartu pertama
    return None

# Mendapatkan gambar kartu berdasarkan nama
@dp.message_handler(lambda message: message.text.startswith("/card"))
async def get_card(message: types.Message):
    card_name = message.text[len("/card "):].strip()
    card_data = get_card_data(card_name)

    if card_data:
        card_image_url = card_data['card_images'][0]['image_url']
        await message.reply_photo(card_image_url)
    else:
        await handle_error(message)

# Mendapatkan harga terendah dari TCGPlayer
@dp.message_handler(lambda message: message.text.startswith("/price"))
async def get_price(message: types.Message):
    card_name = message.text[len("/price "):].strip()
    card_data = get_card_data(card_name)

    if card_data:
        price = card_data['card_prices'][0]['tcgplayer_price']
        await message.reply(f'TCGPlayer Price: ${price}')
    else:
        await handle_error(message)

# Mendapatkan efek kartu
@dp.message_handler(lambda message: message.text.startswith("/effect"))
async def get_effect(message: types.Message):
    card_name = message.text[len("/effect "):].strip()
    card_data = get_card_data(card_name)

    if card_data:
        card_info = f"Name: {card_data['name']}\nEffect: {card_data['desc']}"
        await message.reply(card_info)
    else:
        await handle_error(message)

# Mendapatkan informasi kartu
@dp.message_handler(lambda message: message.text.startswith("/stats"))
async def get_stats(message: types.Message):
    card_name = message.text[len("/stats "):].strip()
    card_data = get_card_data(card_name)

    if card_data:
        info = f"Name: {card_data['name']}\nCard Type: {card_data['type']}\nSubtype: {card_data['race']}\n"
        
        if card_data.get('archetype'):
            info += f"Archetype: {card_data['archetype']}\n"

        if card_data['type'] not in [CARD_TYPES['SPELL'], CARD_TYPES['TRAP']]:
            if "XYZ" in card_data['type']:
                info += f"Rank: {card_data['level']}\n"
            elif "Link" in card_data['type']:
                info += f"Link Rating: {card_data['linkval']}\nLink Markers: {' | '.join(card_data['linkmarkers'])}\n"
            else:
                info += f"Level: {card_data['level']}\n"

            info += f"Attribute: {card_data['attribute']}\nType: {card_data['race']}\nAttack: {card_data['atk']}\n"

            if "Link" not in card_data['type']:
                info += f"Defense: {card_data['def']}\n"

            if "Pendulum" in card_data['type']:
                info += f"Pendulum Scale: {card_data['scale']}\n"

        if card_data.get('banlist_info') and card_data['banlist_info'].get('ban_tcg'):
            info += f"Banlist Status: {card_data['banlist_info']['ban_tcg']}\n"

        await message.reply(info)
    else:
        await handle_error(message)

# Mendapatkan semua karya seni dari kartu
@dp.message_handler(lambda message: message.text.startswith("/artworks"))
async def get_artworks(message: types.Message):
    card_name = message.text[len("/artworks "):].strip()
    card_data = get_card_data(card_name)

    if card_data:
        images = [InputMediaPhoto(media=img['image_url']) for img in card_data['card_images']]
        await bot.send_media_group(chat_id=message.chat.id, media=images)
    else:
        await handle_error(message)

# Menggambar kartu acak
@dp.message_handler(commands=['draw'])
async def draw_card(message: types.Message):
    response = requests.get("https://db.ygoprodeck.com/api/v7/randomcard.php")

    if response.status_code == 200:
        data = response.json()  # Ambil data JSON

        if data and isinstance(data, dict) and 'data' in data and len(data['data']) > 0:  # Memastikan data valid
            card = data['data'][0]
            caption = "MONSUTA CADO!!!" if card['type'] not in [CARD_TYPES['SPELL'], CARD_TYPES['TRAP']] else ""
            await message.reply_photo(card['card_images'][0]['image_url'], caption=caption)
        else:
            await handle_error(message)  # Jika data tidak valid
    else:
        await handle_error(message)  # Jika permintaan API gagal

# Memulai bot
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
