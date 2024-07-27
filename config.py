import os

class Config:
    API_ID = os.getenv('API_ID', '21740783')
    API_HASH = os.getenv('API_HASH', 'a5dc7fec8302615f5b441ec5e238cd46')
    BOT_TOKEN = os.getenv('BOT_TOKEN', '7116266807:AAFiuS4MxcubBiHRyzKEDnmYPCRiS0f3aGU')
    OWNER_USERNAME = '@speedwolf'
    IS_PREMIUM = False  # Set to True if you have a premium account
# Directories for file storage
    DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', 'downloads')
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'outputs')
    DOWNLOAD_PATH = "downloads/"

# Directory paths for downloading and saving files
    DOWNLOAD_DIR = 'downloads'  # Directory to save downloaded videos
    OUTPUT_DIR = 'outputs'  # Directory to save extracted audio files

# Flask configuration
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
