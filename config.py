import os

class Config:
    # Telegram API settings
    API_ID = os.getenv('API_ID', '21740783')  # Replace with your API ID
    API_HASH = os.getenv('API_HASH', 'a5dc7fec8302615f5b441ec5e238cd46')  # Replace with your API Hash
    BOT_TOKEN = os.getenv('BOT_TOKEN', '7116266807:AAFiuS4MxcubBiHRyzKEDnmYPCRiS0f3aGU')  # Replace with your Bot Token

    # Flask settings
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

    # Directory settings
    TEMP_DIR = os.getenv('TEMP_DIR', '/tmp')
    
    # FFmpeg settings (Optional: Adjust if needed)
    FFMPEG_COMMAND = 'ffmpeg'
    
    # Other settings (Optional)
    DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Instantiate the config class
config = Config()
