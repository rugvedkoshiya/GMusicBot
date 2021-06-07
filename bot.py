import re
import os
import json
import logging
import requests
from typing import Dict
from telegram import Update, Bot, error
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from config import TestingConfig as BOT_SETTING
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import audioProvider
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError
import siaskynet as skynet
import wget



# .env Configuration
BOT_AUTH = Bot(BOT_SETTING.TOKEN)

# Spotify Client
cid = BOT_SETTING.SPOTIFY_CLIENT_ID
secret = BOT_SETTING.SPOTIFY_CLIENT_SECRET
client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Heyy! I am GMusic Official Bot v1.2')


def help(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('No one will help you :)')


def get_youtube_link(song_name: str, song_artists: str, song_album: str, duration: str):
    youtube_link = audioProvider.search_and_get_best_match(
        song_name, song_artists, song_album, duration
    )
    if youtube_link is None:
        # raise Exception("Could not match any of the results on YouTube")
        # print("Could not match any of the results on YouTube. Skipping")
        return None
    else:
        # print(youtube_link)
        return youtube_link


def text_handler(update: Update, context: CallbackContext) -> None:
    try:
        if context.user_data['auth'] == BOT_SETTING.AUTH:
            update.message.reply_text('I am on it 😇')
            # print(update.message.chat_id)
            user_text = update.message.text

            # Call Spotify for Metadata
            response = sp.track(user_text)
            spotify_id = response["id"]
            spotify_name = response["name"]
            spotify_artists = []
            for artist in response["artists"]:
                spotify_artists.append(artist["name"])
            spotify_album = response["album"]["name"]
            spotify_img = response["album"]["images"][0]["url"]
            duration = round(response["duration_ms"] / 1000, ndigits=3)
            displayName = spotify_name + " - " + ", ".join(spotify_artists)

            # Check that music is avilable or not
            res = database_check(spotify_id)
            if res == True:
                # Call Youtube search
                update.message.reply_text('Finding on Youtube... 🔎')
                youtube_link = get_youtube_link(spotify_name, spotify_artists, spotify_album, duration)
                print(youtube_link)
                update.message.reply_text("Here what I found 👀")
                update.message.reply_text(youtube_link)

                # Download from Youtube
                update.message.reply_text("Song Downloading... 😎")
                if youtube_link != None:
                    ydl_opts = {
                        'format': "251/bestaudio",
                        'outtmpl': f"{spotify_id}.webm"
                    }
                    with YoutubeDL(ydl_opts) as ydl:
                        try:
                            ydl.download([youtube_link])

                            # Upload to Siasky.net
                            update.message.reply_text("Song Uploading... 📤")
                            client = skynet.SkynetClient()
                            skylink_music = client.upload_file(f"{spotify_id}.webm")
                            os.remove(f"{spotify_id}.webm")
                            update.message.reply_text("Song Upload successful\nsiasky.net/" + skylink_music[6:])
                            update.message.reply_text("Poster Downloading... 😎")
                            spotify_poster = wget.download(spotify_img)
                            update.message.reply_text("Poster Uploading... 📤")
                            skylink_poster = client.upload_file(spotify_poster)
                            os.remove(spotify_poster)
                            update.message.reply_text("Poster Upload successful\nsiasky.net/" + skylink_music[6:])

                            # Update Database
                            res = database_entry(spotify_id, spotify_album, spotify_artists, spotify_name, skylink_music[6:], skylink_poster[6:])
                            if res != None:
                                update.message.reply_text("Done 🤝")
                            else:
                                update.message.reply_text("Database Error 😥")

                        except DownloadError:
                            # print("requested format not available")
                            update.message.reply_text("Something went wrong with this song try another song")
                        except Exception as e:
                            # print("errr")
                            print(e)
                            update.message.reply_text("Ohh...\nContact Admin\nI'm Sick 🤒")
                else:
                    update.message.reply_text("Ek baat batau...\nThis song is not on Youtube\nI know you sended spotify link but....😝\nI hope you understand that I am not Mr. Grey I am his creation 🙂")
            elif res == False:
                update.message.reply_text("This music is already uploaded :)")
            else:
                update.message.reply_text("I'm not able to check that this song is already exist or not\nSave me from Mr. Grey 🥺")
    except KeyError:
        update.message.reply_text("Do I know you 🤨")
    except Exception as e :
        print(e)


def database_entry(spotify_id, album, artist, name, siasky_music, siasky_poster):
    headers = {}
    data = {
        "spotify_id": spotify_id,
        "album": album,
        "artist": artist,
        "name": name,
        "music": siasky_music,
        "poster": siasky_poster,
        "auth": BOT_SETTING.GMUSIC_API_KEY,
    }
    response = requests.post(BOT_SETTING.GMUSIC_API_ADD_URL, headers = headers, data = data)
    if response.status_code == 200:
        return response.json()["id"]
    else:
        return None


def database_check(spotify_id):
    headers = {}
    data = {
        "spotify_id": spotify_id,
        "auth": BOT_SETTING.GMUSIC_API_KEY,
    }
    response = requests.post(BOT_SETTING.GMUSIC_API_CHECK_URL, headers = headers, data = data)
    if response.status_code == 200:
        return False
    elif response.status_code == 404:
        return True
    else:
        return None



def auth(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    try:
        GMusicAuth = " ".join(context.args)
        if GMusicAuth == BOT_SETTING.AUTH:
            context.user_data['auth'] = GMusicAuth
            text = "Welcome my master 😌"
            # text = facts_to_str(context.user_data)
        else:
            text = "You are not my master :)"
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /auth <Authentication Token> 😒')


def main() -> None:
    """Run bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_SETTING.TOKEN)
    # bot = Bot(TOKEN)
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("auth", auth))
    dispatcher.add_handler(MessageHandler(Filters.text, text_handler))
    # dispatcher.add_handler(CommandHandler("addmusic", addmusic))
    # dispatcher.add_handler(CommandHandler("spotify", spotify_handler))
    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()