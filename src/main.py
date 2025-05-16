from loguru import logger
from pathlib import Path

from sqlalchemy import select, func
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, \
    CallbackQueryHandler, ConversationHandler

from config import settings
from src.database import QuoteOrm, async_session_maker

BASE_DIR = Path(__file__).resolve().parent.parent

logger.add(BASE_DIR.joinpath("logs/logs.log"),
           level="DEBUG",
           rotation="5 MB",
           compression="zip",
           format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                  "<level>{level: <8}</level> | "
                  "<cyan>{function}</cyan>:"
                  "<cyan>{line}</cyan> - "
                  "<level>{message}</level>", )


class Button:
    def __init__(self, text: str, callback: str):
        self.callback_data = callback
        self.text = text


ADD_QUOTE = "add_quote"
RAND_QUOTE = "rand_quote"
CANCEL = "cancel"

ADD_QUOTE_BUTTON = Button("Добавить цитату", ADD_QUOTE)
RAND_QUOTE_BUTTON = Button("Случайная цитата", RAND_QUOTE)
CANCEL_BUTTON = Button("Отменить", CANCEL)

INLINE_KEYBOARD = [[InlineKeyboardButton(text=btn.text, callback_data=btn.callback_data)] for btn in
                   [ADD_QUOTE_BUTTON, RAND_QUOTE_BUTTON]]
INLINE_MARKUP = InlineKeyboardMarkup(INLINE_KEYBOARD)

last_message_id = {}

ADD_QUOTE_FLAG, GET_QUOTE_FLAG = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    last_message_id[chat_id] = update.message.message_id
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Вас приветствует Хранитель Незабытых Цитат. Выберите действие",
                                   reply_markup=INLINE_MARKUP)


@logger.catch
async def press_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    logger.info(f"Button pressed: {query.data}")

    if query.data == ADD_QUOTE:
        await query.edit_message_text(text="Введите цитату", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text=CANCEL_BUTTON.text, callback_data=CANCEL_BUTTON.callback_data)]]))
        return ADD_QUOTE_FLAG
    elif query.data == RAND_QUOTE:
        await query.edit_message_text("Случайная цитата:", reply_markup=INLINE_MARKUP)
        async with async_session_maker() as session:
            query_to_db = select(QuoteOrm).order_by(func.random()).limit(1)
            result = await session.execute(query_to_db)
            quote_obj = result.scalar()
            quote = quote_obj.content if (quote_obj is not None) else "Всё, что обозримо – то не вечно"
            await query.edit_message_text(f"Случайная цитата: {quote}", reply_markup=None)
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f"Выберите действие",
                                           reply_markup=INLINE_MARKUP)
        return ConversationHandler.END
    elif query.data == CANCEL:
        await query.edit_message_text("Действие отменено", reply_markup=None)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Выберите действие",
                                       reply_markup=INLINE_MARKUP)
        return ConversationHandler.END


# Получение имени
async def add_quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_quote = update.message.text
    if new_quote.lower() == "отмена":
        await update.message.reply_text("Действие отменено", reply_markup=INLINE_MARKUP)
        return ConversationHandler.END

    async with async_session_maker() as session:
        quote = QuoteOrm(content=new_quote)
        session.add(quote)
        await session.commit()
    await update.message.reply_text("Цитата сохранена", reply_markup=INLINE_MARKUP)
    return ConversationHandler.END


# Завершение беседы
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Беседа отменена. Если хочешь начать заново, напиши /start.")
    return ConversationHandler.END


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"username: {update.effective_user.username}")
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=update.message.text)


@logger.catch
def main():
    application = ApplicationBuilder().token(settings.TG_BOT_TOKEN).build()
    logger.success("Application built")

    # Определение обработчиков
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(press_button)],
        states={
            ADD_QUOTE_FLAG: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_quote)],
            # GET_QUOTE_FLAG: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quote)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(conv_handler)

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    application.add_handler(CallbackQueryHandler(press_button))
    # button_handler = CallbackQueryHandler(press_button)
    # application.add_handler(button_handler)
    # echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), get_message)
    # application.add_handler(echo_handler)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    application.add_handler(echo_handler)
    logger.success("Handlers added")

    application.run_polling()
