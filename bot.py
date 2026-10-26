import re
import requests
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Твой токен от BotFather
TOKEN = '8884505602:AAGnkxc42iTw_Ni41uxB89gCOMRddQBA37Q'
bot = telebot.TeleBot(TOKEN)


def search_terraria_wiki(query):
  """Поиск с поддержкой инлайн-кнопок и картинок"""
  is_russian = bool(re.search('[а-яА-ЯёЁ]', query))
  headers = {'User-Agent': 'TerrariaWikiBot/1.0'}

  if is_russian:
    base_url = 'https://terraria-game.fandom.com/ru/api.php'
  else:
    base_url = 'https://terraria.wiki.gg/api.php'

  params = {
      'action': 'opensearch',
      'search': query,
      'limit': 1,
      'namespace': 0,
      'format': 'json',
  }

  try:
    response = requests.get(base_url, params=params, headers=headers)
    data = response.json()

    if not data or len(data) < 4 or not data[1]:
      return None, None, None, None

    title = data[1][0]
    description = (
        data[2][0]
        if data[2][0]
        else 'Смотрите подробную информацию на странице вики по ссылке ниже.'
    )
    url = data[3][0]

    img_params = {
        'action': 'query',
        'prop': 'pageimages',
        'piprop': 'original',
        'titles': title,
        'format': 'json',
    }
    img_resp = requests.get(base_url, params=img_params, headers=headers)
    img_data = img_resp.json()
    pages = img_data.get('query', {}).get('pages', {})
    image_url = None
    for p_id, p_info in pages.items():
      if 'original' in p_info:
        image_url = p_info['original']['source']

    return title, description, url, image_url

  except Exception as e:
    print(f'Ошибка при поиске: {e}')
    return None, None, None, None


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
  bot.reply_to(
      message,
      'Привет! Я твой интерактивный справочник по Террарии с красивым оформлением.\n\nНапиши'
      ' название предмета или босса (например: *Лунный лорд*, *Зенит*).',
  )


@bot.message_handler(func=lambda message: True)
def handle_query(message):
  query = message.text.strip()
  bot.send_message(message.chat.id, f'🔍 Ищу "{query}"...')

  title, text, url, image_url = search_terraria_wiki(query)

  if not title:
    bot.send_message(
        message.chat.id,
        'К сожалению, по твоему запросу ничего не нашлось. Попробуй уточнить'
        ' название.',
    )
    return

  if len(text) > 3000:
    text = text[:3000] + '...\n\n*(текст сокращен)*'

  # Создаем красивую интерактивную кнопку
  markup = InlineKeyboardMarkup()
  markup.add(InlineKeyboardButton('🔗 Читать на Вики', url=url))

  try:
    if image_url:
      bot.send_photo(
          message.chat.id,
          image_url,
          caption=f'📖 **{title}**',
          parse_mode='Markdown',
      )
      bot.send_message(
          message.chat.id,
          text,
          reply_markup=markup,
          disable_web_page_preview=True,
      )
    else:
      bot.send_message(
          message.chat.id,
          f'📖 **{title}**\n\n{text}',
          reply_markup=markup,
          parse_mode='Markdown',
          disable_web_page_preview=True,
      )
  except Exception as e:
    print(f'Ошибка отправки сообщения: {e}')


print('🤖 Бот с кнопками и красивым интерфейсом успешно запущен!')
bot.polling(none_stop=True)