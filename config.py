import os

API_ID = os.getenv('API_ID', '21740783')
API_HASH = os.getenv('API_HASH', 'a5dc7fec8302615f5b441ec5e238cd46')
BOT_TOKEN = os.getenv('BOT_TOKEN', '7116266807:AAFiuS4MxcubBiHRyzKEDnmYPCRiS0f3aGU')
import os

# Telegram API credentials
API_ID = os.getenv('API_ID', 'YOUR_API_ID')
API_HASH = os.getenv('API_HASH', 'YOUR_API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN')

# Directories for file storage
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', 'downloads')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')

# Flask configuration
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
