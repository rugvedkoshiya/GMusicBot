class Config():
    SPOTIFY_CLIENT_ID="Spotify ID"
    SPOTIFY_CLIENT_SECRET="Spotify Secret"
    GMUSIC_API_ADD_URL="https://gmusicflaskapi.herokuapp.com/addMusic"
    GMUSIC_API_CHECK_URL="https://gmusicflaskapi.herokuapp.com/check"
    GMUSIC_API_KEY="Authentication Token for GMusicAPI"

class TestingConfig(Config):
    AUTH="Testing Auth Code"
    TOKEN="Telegram Test Bot Token"

class ProductionConfig(Config):
    AUTH="Production Auth Code"
    TOKEN="Telegram Production Bot Token"