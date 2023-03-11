from setup import get_settings
# from tabulate import tabulate
from time import sleep
import schedule
from telegram.ext import filters, Updater, MessageHandler, CommandHandler, ContextTypes, Application
from telegram import __version__ as TG_VER, Update
import logging
import os


try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

# Enable logging
logging.basicConfig(
    format="[%(asctime)s] - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class GraceBot:

    def __init__(self, bot_token: str, ngrok_authtoken: str, ngrok_subdomain: str, port: str) -> None:
        # Create the Application and pass it your bot's token.
        self.application = Application.builder().token(bot_token).build()

        # on different commands - answer in Telegram
        self.application.add_handler(CommandHandler(["start", "help"], self.start))
        self.application.add_handler(CommandHandler("buy", self.buy_order))
        self.application.add_handler(CommandHandler("sell", self.sell_order))
        self.application.add_handler(CommandHandler("status", self.send_order_status))
        self.application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.echo))

        # Run the bot until the user presses Ctrl-C
        self.application.run_polling()

        ngrok_subdomain = os.environ.get('NGROK_SUBDOMAIN')
        webhook_url = f'https://{ngrok_subdomain}.ngrok.io/{ngrok_authtoken}'
        logging(webhook_url)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Sends explanation on how to use the bot."""
        await update.message.reply_text(
            f"Hi motherfucker! Ready to make some money? You can control me by sending these commands:"
            "/ start / help - to see this message"
            # / status[order_id] - get an updated report for an order
            # / evaluate[symbol] - get a brief analysis on the symbol

            # < b > Alert system < /b >
            # / setalert[order_id] - set an alert if a order is at risk
            # / unsetalert[order_id] - undo / setalert

            # ** Trading commands **
            # /buylt[symbol][limit price] - place a buy limit order
            # / selllt[symbol][limit price] - place a sell limit order
            # / buyst[symbol][stop price] - place a buy stop order
            # / sellst[symbol][stop price] - place a sell stop order"
        )

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """General response to any text send by the user
        """
        chat_id = update.effective_chat.id
        grace_response = "fuck you! speak like a man, pussy "  # + update.message.text
        await context.bot.send_message(chat_id=chat_id, text=grace_response)

    async def send_order_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send an image of the current stock price of the order's symbol + some useful indicators
        """
        if not context.args:
            await update.effective_message.reply_text(f"order_id not provided. Please try again.", quote=True)
            return

        chat_id = update.effective_message.chat_id
        order_id = context.args[0]

        self.my_orders = {chat_id: [order_id]}

        if order_id not in self.my_orders[chat_id]:
            await update.effective_message.reply_text(f"Invalid order. {order_id=} not registered")
            return

        image, caption = generate_report()
        await update.effective_message.reply_photo(image, caption, quote=True)

        # if report_type == 'table':
        #     table = await tabulate(data, headers=headers, tablefmt='orgtbl')
        #     self.send_report(update.message.chat_id, caption='Here is the table:', image_path='table.png')
        # elif report_type == 'chart':
        #     chart = generate_chart()
        #     chart.savefig('chart.png')
        #     self.send_report(update.message.chat_id, caption='Here is the chart:', image_path='chart.png')
        # else:
        #     context.bot.send_message(chat_id=update.effective_chat.id,
        #                              text="Invalid report type. Please choose 'table' or 'chart'.")

    async def set_order_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        context.job_queue.run_custom()

    async def buy_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Add a job to the queue."""
        chat_id = update.effective_message.chat_id
        try:
            # args[0] should contain the time for the timer in seconds
            due = float(context.args[0])
            if due < 0:
                await update.effective_message.reply_text("Sorry we can not go back to future!")
                return

            job_removed = True  # remove_job_if_exists(str(chat_id), context)
            # context.job_queue.run_once(alarm, due, chat_id=chat_id, name=str(chat_id), data=due)

            text = "Timer successfully set!"
            if job_removed:
                text += " Old one was removed."
            await update.effective_message.reply_text(text)

        except (IndexError, ValueError):
            await update.effective_message.reply_text("Usage: /set <seconds>")

    async def sell_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Add a job to the queue."""
        pass

    # def auto_send_report(self):
    #     pass

    def run(self) -> None:
        report_handler = CommandHandler('report', self.generate_report)
        self.dispatcher.add_handler(report_handler)

        self.updater.start_polling()
        self.updater.idle()


def generate_report(image_path: str = 'XAUUSD_2023-03-01_20-45-38.png') -> None:
    # TODO
    dummie = {'price': 1.22543, 'benefit': 1700.42352, 'tp': 10.2324, 'sl': 3.423253}
    caption = "\n".join(f"{ind} = {val:.2f}" for ind, val in dummie.items())
    photo = open(image_path, 'rb')
    return photo, caption


if __name__ == "__main__":
    settings = get_settings("settings\demo\login.json")
    bot_settings = settings["telegram_bot"]

    logger.info(bot_settings)

    grace = GraceBot(**bot_settings)
    # schedule.every(10).minutes.do(grace.send_report, chat_id=chat_id)

    # while True:
    #     schedule.run_pending()
    #     sleep(1)
