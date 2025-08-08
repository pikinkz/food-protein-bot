import logging
import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext.filters import PhotoFilter  # Updated import for Filters
from telegram.ext import CallbackContext

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve API keys from environment variables
API_KEY = os.getenv('TELEGRAM_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi! Send me a picture of your food, and I will track its protein content!')

def process_image(update: Update, context: CallbackContext):
    """Process the image sent by the user and analyze the protein content."""
    # Download the image
    photo_file = update.message.photo[-1].get_file()
    photo_file.download('food_image.jpg')

    # Call Gemini API to analyze the image
    headers = {'Authorization': f'Bearer {GEMINI_API_KEY}'}
    with open('food_image.jpg', 'rb') as f:
        response = requests.post('https://api.gemini.com/food-analyze', files={'file': f}, headers=headers)
        
    if response.status_code == 200:
        data = response.json()
        protein_content = data.get('protein', 'N/A')  # Adjust based on actual Gemini API response
        update.message.reply_text(f'This food contains {protein_content}g of protein.')
    else:
        update.message.reply_text('Sorry, I could not analyze the image. Please try again.')

def main():
    """Start the bot."""
    # Initialize the Updater with the API key
    updater = Updater(API_KEY, use_context=True)
    dp = updater.dispatcher

    # Register the /start command and photo handler
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(PhotoFilter, process_image))  # Updated usage of PhotoFilter

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
