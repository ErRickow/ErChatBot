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
    await message.answer("Card not found", reply_to_message_id=message.message_id)

# Mendapatkan gambar kartu berdasarkan nama
@dp.message_handler(lambda message: message.text.startswith("/card"))
async def get_card(message: types.Message):
    card_name = message.text[len("/card "):].strip()
    response = requests.get(f'https://db.ygoprodeck.com/api/v5/cardinfo.php?name={card_name}')
    
    if response.status_code == 200:
        data = response.json()
        card_image_url = data[0]['card_images'][0]['image_url']
        await message.answer_photo(card_image_url, reply_to_message_id=message.message_id)
    else:
        await handle_error(message)

# Mendapatkan harga terendah dari TCGPlayer
@dp.message_handler(lambda message: message.text.startswith("/price"))
async def get_price(message: types.Message):
    card_name = message.text[len("/price "):].strip()
    response = requests.get(f'https://db.ygoprodeck.com/api/v5/cardinfo.php?name={card_name}')
    
    if response.status_code == 200:
        data = response.json()
        price = data[0]['card_prices'][0]['tcgplayer_price']
        await message.answer(f'TCGPlayer Price: ${price}', reply_to_message_id=message.message_id)
    else:
        await handle_error(message)

# Mendapatkan efek kartu
@dp.message_handler(lambda message: message.text.startswith("/effect"))
async def get_effect(message: types.Message):
    card_name = message.text[len("/effect "):].strip()
    response = requests.get(f'https://db.ygoprodeck.com/api/v5/cardinfo.php?name={card_name}')
    
    if response.status_code == 200:
        data = response.json()
        card_info = f"Name: {data[0]['name']}\nEffect: {data[0]['desc']}"
        await message.answer(card_info, reply_to_message_id=message.message_id)
    else:
        await handle_error(message)

# Mendapatkan informasi kartu
@dp.message_handler(lambda message: message.text.startswith("/stats"))
async def get_stats(message: types.Message):
    card_name = message.text[len("/stats "):].strip()
    response = requests.get(f'https://db.ygoprodeck.com/api/v5/cardinfo.php?name={card_name}')
    
    if response.status_code == 200:
        card = response.json()[0]
        info = f"Name: {card['name']}\nCard Type: {card['type']}\nSubtype: {card['race']}\n"
        
        if card.get('archetype'):
            info += f"Archetype: {card['archetype']}\n"
        
        if card['type'] not in [CARD_TYPES['SPELL'], CARD_TYPES['TRAP']]:
            if "XYZ" in card['type']:
                info += f"Rank: {card['level']}\n"
            elif "Link" in card['type']:
                info += f"Link Rating: {card['linkval']}\nLink Markers: {' | '.join(card['linkmarkers'])}\n"
            else:
                info += f"Level: {card['level']}\n"
            
            info += f"Attribute: {card['attribute']}\nType: {card['race']}\nAttack: {card['atk']}\n"
            
            if "Link" not in card['type']:
                info += f"Defense: {card['def']}\n"
            
            if "Pendulum" in card['type']:
                info += f"Pendulum Scale: {card['scale']}\n"
        
        if card.get('banlist_info') and card['banlist_info'].get('ban_tcg'):
            info += f"Banlist Status: {card['banlist_info']['ban_tcg']}\n"
        
        await message.answer(info, reply_to_message_id=message.message_id)
    else:
        await handle_error(message)

# Mendapatkan semua karya seni dari kartu
@dp.message_handler(lambda message: message.text.startswith("/artworks"))
async def get_artworks(message: types.Message):
    card_name = message.text[len("/artworks "):].strip()
    response = requests.get(f'https://db.ygoprodeck.com/api/v5/cardinfo.php?name={card_name}')
    
    if response.status_code == 200:
        data = response.json()
        images = [InputMediaPhoto(media=img['image_url']) for img in data[0]['card_images']]
        await bot.send_media_group(chat_id=message.chat.id, media=images, reply_to_message_id=message.message_id)
    else:
        await handle_error(message)

# Menggambar kartu acak
@dp.message_handler(commands=['draw'])
async def draw_card(message: types.Message):
    response = requests.get("https://db.ygoprodeck.com/api/v5/randomcard.php")
    
    if response.status_code == 200:
        card = response.json()[0]
        caption = "MONSUTA CADO!!!" if card['type'] not in [CARD_TYPES['SPELL'], CARD_TYPES['TRAP']] else ""
        await message.answer_photo(card['card_images'][0]['image_url'], caption=caption, reply_to_message_id=message.message_id)
    else:
        await handle_error(message)

# Memulai bot
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
