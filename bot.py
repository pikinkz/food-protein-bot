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
    try:
        url = f"https://api.telegram.org/bot{API_KEY}/deleteWebhook"
        response = requests.post(url)
        if response.status_code == 200:
            logger.info("Webhook cleared successfully.")
        else:
            logger.error(f"Failed to clear webhook: {response.text}")
    except Exception as e:
        logger.error(f"Error clearing webhook: {e}")

# Ensure no other instances are running by checking for active sessions
def ensure_no_other_instance():
    try:
        url = f"https://api.telegram.org/bot{API_KEY}/getUpdates"
        response = requests.get(url)
        if response.status_code == 200:
            updates = response.json()
            if updates["result"]:
                logger.warning("Previous bot instance is active. Please clear the sessions.")
        else:
            logger.error(f"Failed to check bot status: {response.text}")
    except Exception as e:
        logger.error(f"Error checking bot status: {e}")

async def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    logger.info("Received /start command")
    await update.message.reply_text('Hi! Send me a picture of your food, and I will track its protein content!')

async def process_image(update: Update, context: CallbackContext):
    """Process the image sent by the user and analyze the protein content."""
    logger.info(f"Received image: {update.message.photo[-1].file_id}")

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
        await update.message.reply_text(f'This food contains {protein_content}g of protein.')
        logger.info(f"Protein content: {protein_content}g")
    else:
        await update.message.reply_text('Sorry, I could not analyze the image. Please try again.')
        logger.error(f"Error analyzing image: {response.text}")

def main():
    """Start the bot."""
    # Clear any existing webhook to prevent conflicts
    clear_webhook()

    # Ensure no other instances are running before starting the bot
    ensure_no_other_instance()

    # Initialize the Application with the API key
    application = Application.builder().token(API_KEY).build()

    # Register the /start command and photo handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, process_image))

    logger.info("Starting bot polling...")
    try:
        application.run_polling()
        logger.info("Bot started successfully with polling.")
    except Exception as e:
        logger.error(f"Error in polling: {e}")
        raise e

if __name__ == '__main__':
    main()
