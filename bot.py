import logging
import os
import requests
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, Application
from telegram.ext import CallbackContext

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve API keys from environment variables
API_KEY = os.getenv('TELEGRAM_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Clear any existing updates when the bot starts
def clear_updates():
    url = f"https://api.telegram.org/bot{API_KEY}/getUpdates"
    response = requests.get(url)
    if response.status_code == 200:
        updates = response.json().get("result", [])
        if updates:
            # Mark all updates as read (effectively clears them)
            for update in updates:
                update_id = update.get("update_id")
                requests.post(f"https://api.telegram.org/bot{API_KEY}/getUpdates?offset={update_id + 1}")
            logger.info("Cleared previous updates successfully.")
    else:
        logger.error("Failed to clear updates")

# Handle the /start command
async def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi! Send me a picture of your food, and I will track its protein content!')

# Handle the image processing and protein content analysis
async def process_image(update: Update, context: CallbackContext):
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
        await update.message.reply_text(f'This food contains {protein_content}g of protein.')
    else:
        await update.message.reply_text('Sorry, I could not analyze the image. Please try again.')

# Main function to start the bot
def main():
    """Start the bot."""
    # Clear previous updates each time the bot starts
    clear_updates()

    # Initialize the Application with the API key
    application = Application.builder().token(API_KEY).build()

    # Register the /start command and photo handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, process_image))

    # Start the bot with proper exception handling to avoid duplicate instances
    try:
        application.run_polling()
    except Exception as e:
        logger.error(f"Error in polling: {e}")
        raise e

if __name__ == '__main__':
    main()
