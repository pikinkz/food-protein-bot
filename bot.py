import logging
import os
import requests
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters
from telegram.ext import Application, CallbackContext

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve API keys from environment variables
API_KEY = os.getenv('TELEGRAM_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Ensure the webhook is removed before running the bot
def clear_webhook():
    url = f"https://api.telegram.org/bot{API_KEY}/deleteWebhook"
    response = requests.post(url)
    return response.json()

async def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi! Send me a picture of your food, and I will track its protein content!')

async def process_image(update: Update, context: CallbackContext):
    """Process the image sent by the user and analyze the protein content."""
    try:
        # Download the image
        photo_file = await update.message.photo[-1].get_file()  # Await the coroutine here
        await photo_file.download('food_image.jpg')  # Now you can download it

        # Call Gemini API to analyze the image
        headers = {'Authorization': f'Bearer {GEMINI_API_KEY}'}
        with open('food_image.jpg', 'rb') as f:
            response = requests.post('https://api.gemini.com/food-analyze', files={'file': f}, headers=headers)

        if response.status_code == 200:
            data = response.json()
            protein_content = data.get('protein', 'N/A')  # Adjust based on actual Gemini API response
            await update.message.reply_text(f'This food contains {protein_content}g of protein.')
        else:
            logger.error(f"Gemini API response error: {response.text}")
            await update.message.reply_text('Sorry, I could not analyze the image. Please try again.')
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text('There was an error processing the image. Please try again.')

def main():
    """Start the bot and ensure it works properly."""
    clear_webhook()  # Ensure the webhook is cleared

    # Initialize the bot with the correct API token
    application = Application.builder().token(API_KEY).build()
    logger.info("Bot polling initiated")

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, process_image))

    try:
        logger.info("Starting polling...")
        application.run_polling()
    except Exception as e:
        logger.error(f"Error in polling: {e}")
        raise e

if __name__ == '__main__':
    main()
