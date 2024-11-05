import logging
import random
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Настройки логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки Telegram
TOKEN = '6485208774:AAFZGg38WknfhrQMabVH1naJszJxU8bDJOI'

# Настройки Spotify
SPOTIFY_CLIENT_ID = 'efb4c646267c40c298686785b9f5a3a1'
SPOTIFY_CLIENT_SECRET = 'a263e968e5cc4d0db8422403af4782af'



# Настройки Genius
GENIUS_API_TOKEN = 'i88AmXnc3H_ha5CBKqH4Krk0ql8CwsLLjabYrvDWsPxHCW1-wg1GsRzeQt7GdasY'

# Инициализация Spotify клиента
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

# Словари для хранения игр
hangman_games = {}
music_games = {}

class MusicGame:
    def __init__(self):
        self.current_track = None
        self.is_active = False

    def reset(self):
        self.current_track = None
        self.is_active = False

def get_lyrics(song_name, artist_name):
    headers = {'Authorization': f'Bearer {GENIUS_API_TOKEN}'}
    search_url = 'https://api.genius.com/search'
    response = requests.get(search_url, headers=headers, params={'q': f"{song_name} {artist_name}"})
    json_response = response.json()
    
    if json_response['response']['hits']:
        song_path = json_response['response']['hits'][0]['result']['path']
        song_url = f'https://genius.com{song_path}'
        
        # Получаем текст песни с Genius
        page = requests.get(song_url)
        soup = BeautifulSoup(page.text, 'html.parser')
        lyrics = soup.find('div', class_='lyrics')
        
        if lyrics:
            return lyrics.get_text()
    
    return "Не удалось получить текст песни."

async def musicgame_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id in music_games:
        await update.message.reply_text("Игра уже идет!")
        return

    music_games[chat_id] = MusicGame()
    game = music_games[chat_id]
    game.is_active = True

    # Получаем случайный плейлист
    playlists = spotify.user_playlists('spotify')
    playlist = random.choice(playlists['items'])
    
    # Получаем треки из плейлиста
    tracks = spotify.playlist_tracks(playlist['id'])
    track = random.choice(tracks['items'])['track']

    game.current_track = {
        'name': track['name'],
        'artist': track['artists'][0]['name']
    }

    # Получаем текст песни
    lyrics = get_lyrics(game.current_track['name'], game.current_track['artist'])
    if lyrics != "Не удалось получить текст песни.":
        lyrics_lines = lyrics.split('\n')
        sample_line = random.choice(lyrics_lines).strip()
    else:
        sample_line = "К сожалению, текст песни недоступен."

    await update.message.reply_text(f"🎵 Угадайте песню! Вот одна из строчек:\n{sample_line}\nУ вас 30 секунд.")

    await asyncio.sleep(30)

    if chat_id in music_games:
        await update.message.reply_text(f"Время вышло! Это была песня {game.current_track['name']} - {game.current_track['artist']}")
        del music_games[chat_id]

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    
    # Если идет игра в угадай мелодию
    if chat_id in music_games:
        await update.message.reply_text("Пожалуйста, угадайте песню!")
    else:
        await update.message.reply_text("Сначала начните игру! Используйте /musicgame")

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("Привет! Используйте /musicgame, чтобы начать игру.")))
    application.add_handler(CommandHandler("musicgame", musicgame_start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    application.run_polling()

if __name__ == '__main__':
    main()
