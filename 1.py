# ```


from telegram import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler, ConversationHandler
import sqlite3
import asyncio

DATE_START, DATE_END, GUESTS, ROOM_TYPE = range(4)

application = Application.builder().token('7262756924:AAH_6DAGNlDKHIbtVDxoPUVtUMeW44STSac').build()


# -----------------------------------------------------------------------------------------------------------------------
def setup_database():
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Створення таблиці користувачів
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        chat_id INTEGER NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Створення таблиці бронювань
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date_start TEXT NOT NULL,
        date_end TEXT NOT NULL,
        guests INTEGER NOT NULL,
        room_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    connection.commit()
    connection.close()
    print("База даних успішно налаштована.")


def add_user(username, chat_id):
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO users (username, chat_id)
        VALUES (?, ?)
        """, (username, chat_id))
        connection.commit()
        print(f"Користувач {username} успішно доданий.")
    except sqlite3.Error as e:
        print(f"Помилка при додаванні користувача: {e}")
    finally:
        connection.close()


def get_all_users():
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    cursor.execute("SELECT chat_id FROM users")
    users = cursor.fetchall()
    connection.close()
    return [user[0] for user in users]


async def broadcast_message(update, context):
    users = get_all_users()
    message = "spam hahahahahaahahha"
    successful = 0
    failed = 0

    for chat_id in users:
        try:
            await context.bot.send_message(chat_i=chat_id, text=message)
            successful += 1
        except Exception as e:
            print(f" no send message {chat_id}: {e}")
            failed += 1
        await asyncio.sleep(0.1)  # додати затримку для уникнення лимиту телеграма
    await update.message.reply_text(f"newsletter end. very good {successful}, unsuccessful:{failed}")


# ---------------------------------------------------------------------------------------------
# команда/start с привествием сообщением и кнопками
async def start_command(update, context):
    user_name = update.effective_user.username or "NoUsername"
    chat_id = update.effective_user.id
    add_user(user_name, chat_id)

    inline_keyboard = [
        [InlineKeyboardButton("поставить таймер ", callback_data="books")],
        [InlineKeyboardButton("помощь автору ", callback_data="services")],
        [InlineKeyboardButton("под услуги", callback_data="date_start")],
        [InlineKeyboardButton("mem", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard)

    # табличка после старта

    await update.message.reply_text("ПРИВЕТ Я БОТ НАПОНИНАНИЙ",
                                    reply_markup=markup)


# -----------------------------------------------------------------------------------------------------------------------


# Обработчик действий с конопок

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "books":
        await query.message.reply_text("Для бронирования номера введите дату заезда (например, 2023-12-01):")
        return DATE_START
    elif query.data == "services":
        await  query.message.reply_text(
            "Помоги автору своим деньгами\n"
            "Visa '4441 1111 2776 4961'\n")
        return ConversationHandler.END

    elif query.data == "help":
        await  query.message.reply_text(" могу чем-то помочь ")
        return ConversationHandler.END

    # Сбор данных для бронирования


async def date_start(update, context):
    context.user_data['date_start'] = update.message.text
    await update.message.reply_text("Введите дату напоминания (например, 2023-12-10):")
    return DATE_END


async def date_end(update, context):
    context.user_data['date_end'] = update.message.text
    await update.message.reply_text("Сколько гостей будет проживать?")
    return GUESTS


async def guests(update, context):
    context.user_data['guests'] = update.message.text
    reply_keyboard = [["Стандарт", "Люкс", "Семейный"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Выберите тип номера:", reply_markup=markup)
    return ROOM_TYPE


async def room_type(update, context):
    context.user_data['room_type'] = update.message.text
    booking_details = (
        f"Ваши данные для бронирования:\n"
        f"- Дата заезда: {context.user_data['date_start']}\n"
        f"- Дата выезда: {context.user_data['date_end']}\n"
        f"- Количество гостей: {context.user_data['guests']}\n"
        f"- Тип номера: {context.user_data['room_type']}\n"
        "Если все верно, наш администратор свяжется с вами для подтверждения.")
    await update.message.reply_text(booking_details, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ------------------------------------------------------------------------------------------------------------

async def cancel(update, context):
    await update.message.reply_text("Бронирование отменено. Возвращайтесь, когда будете готовы!",
                                    reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


booking_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_handler, pattern="^(books|services|help)$")],
    states={
        DATE_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_start)],
        DATE_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_end)],
        GUESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, guests)],
        ROOM_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, room_type)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_user=True
)


# -----------------------------------------------------------------------------------------------------------------------


async def send_photos(update, context):
    # шляхи до локальних файлів
    photo_paths = ["image/time1.jpg"]

    # Перевірка на існування файлів
    try:
        media_group = [InputMediaPhoto(open(photo, "rb")) for photo in photo_paths]
        await update.message.reply_media_group(media_group)

    except FileNotFoundError as e:
        await update.message.reply_text(f"ОШИБКА: ФАЙЛ {e.filename} не знайдено.")

    except Exception as e:
        await update.message.reply.text(f"bbfghfg: {str(e)}")


# -----------------------------------------------------------------------------------------------------------------------
# команды чтобы бот работал


def main():
    setup_database()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(booking_handler)
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("send_photos", send_photos))

    application.run_polling()


# -----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    main()

# ```
