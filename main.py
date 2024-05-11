import sqlite3
import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    InputFile, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from telegram import ParseMode
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
import sqlite3
from telegram import Bot

# Токен вашего бота (замените на реальный токен)
TOKEN = 'token'

# Подключение к базе данных SQLite
conn = sqlite3.connect('dating_bot.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER,
        gender TEXT,
        city TEXT,
        bio TEXT,
        photo_path TEXT  -- Add this line for the new column
    )

''')
conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS likes (
        user_id INTEGER,
        liked_user_id INTEGER,
        PRIMARY KEY (user_id, liked_user_id)
    )
''')
conn.commit()



def start(update: Update, context: CallbackContext) -> None:
    user_id = None

    if update.message:
        # If the command is triggered by a regular message
        user_id = update.message.from_user.id
    elif update.callback_query and update.callback_query.from_user:
        # If the command is triggered by a callback query
        user_id = update.callback_query.from_user.id

    if user_id:
        if is_user_registered(user_id):
            # User is already registered
            keyboard = [
                [KeyboardButton("Начать поиск")],
                [KeyboardButton("Удалить анкету")],
                [KeyboardButton("Моя анкета")],
                [KeyboardButton("Информация")]
            ]

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            context.bot.send_message(user_id, "Выберите действие:", reply_markup=reply_markup)
        else:
            # User is not registered
            info(update, context)
            context.bot.send_message(user_id, "Добро пожаловать в Бот Знакомств!\nДля начала, воспользуйтесь командой /register.")
    else:
        # Log an error or handle the situation when user ID is not available
        print("Error: User ID not available in the update object.")



from telegram import InputFile

def info(update: Update, context: CallbackContext) -> None:
    # Get the user ID
    user_id = 728362175

    # Get the username for contact information
    user_profile_username = get_username_from_id(context.bot, user_id)

    # Formulate the information message
    info_message = (
        "Используя данный бот, пользователь соглашается с пользовательским соглашением - "
        "https://telegra.ph/Polzovatelskoe-soglashenie-01-11-3\n\n"
        "Используя данный бот, пользователь подтверждает, что ему исполнилось 16 лет и он в состоянии мыслить рационально.\n\n"
        f"По любым вопросам, обращаться к @{user_profile_username}.\n\n"
        f"Если Вы хотите поддержать проект, также обращаться к @{user_profile_username}."
    )

    # Send the information message
    context.bot.send_message(chat_id=update.effective_chat.id, text=info_message)

def my_profile(update: Update, context: CallbackContext) -> None:
    print("start my profile")

    user_id = None

    if update.message:
        # If the command is triggered by a regular message
        user_id = update.message.from_user.id
    elif update.callback_query and update.callback_query.from_user:
        # If the command is triggered by a callback query
        user_id = update.callback_query.from_user.id

    if user_id:
        user_data = get_user_data(user_id)
        if user_data:
            # Format the user data for display
            profile_info = (
                f"Имя: {user_data['name']}\n"
                f"Возраст: {user_data['age']}\n"
                f"Пол: {user_data['gender']}\n"
                f"Город: {user_data['city']}\n"
                f"Биография: {user_data['bio']}\n"
            )
            photo_path = user_data.get('photo_path')
            if photo_path:
                photo_file = open(photo_path, 'rb')
                context.bot.send_photo(user_id, photo_file)
            else:
                profile_info += "Фото: Нет фото"

            if update.message:
                update.message.reply_text(profile_info)
            elif update.callback_query:
                update.callback_query.message.reply_text(profile_info)
        else:
            if update.message:
                update.message.reply_text("Вы еще не зарегистрированы. Используйте /register для создания анкеты.")
            elif update.callback_query:
                update.callback_query.message.reply_text(
                    "Вы еще не зарегистрированы. Используйте /register для создания анкеты.")


def start_browsing(update: Update, context: CallbackContext) -> None:
    browse(update, context)
    show_keyboard(update, context)


def process_text_message(update: Update, context: CallbackContext) -> None:
    # Получите текст сообщения
    text = update.message.text

    # Здесь вы можете добавить логику для обработки текстовых сообщений и вызов соответствующих функций
    if text.lower() == 'начать поиск':
        browse(update, context)
        show_keyboard(update, context)
    elif text.lower() == 'удалить анкету':
        delete_user_data(update.message.from_user.id)
        update.message.reply_text("Ваша анкета удалена. Вы можете зарегистрироваться заново с помощью /register.")
    elif text.lower() == 'моя анкета':
        my_profile(update, context)
    elif text.lower() == 'меню':
        start(update, context)
    elif text.lower() == 'Дальше':
        browse(update, context)
        show_keyboard(update, context)


def like(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    try:
        # Extracting profile_id from the callback data
        if isinstance(query.data, str):
            _, profile_id_str = query.data.split('_')
            profile_id = int(profile_id_str)

            print(f"Debug: Processing like for user {user_id} and profile {profile_id}")

            # Check if the like entry already exists
            if check_like(user_id, profile_id):
                context.bot.send_message(chat_id=user_id, text=f"Вы уже лайкнули этого пользователя.")
            else:
                # Insert the like into the database
                insert_like(user_id, profile_id)
                context.bot.send_message(chat_id=user_id, text=f"Лайк учтен! Давайте продолжим!")

                # Check for mutual like
                if check_like(profile_id, user_id):
                    user_profile_username = get_username_from_id(context.bot, user_id)
                    profile_profile_username = get_username_from_id(context.bot, profile_id)
                    print(user_profile_username)
                    print(profile_profile_username)
                    # Notify the users about mutual like
                    mutual_like_message_user = f'Ура! 🎉 Взаимный лайк с @{profile_profile_username}! Начните общение!'
                    mutual_like_message_profile = f'Ура! 🎉 Взаимный лайк с @{user_profile_username}! Начните общение!'

                    # Send messages directly using context.bot.send_message
                    context.bot.send_message(chat_id=user_id, text=mutual_like_message_user)
                    context.bot.send_message(chat_id=profile_id, text=mutual_like_message_profile)
                else:
                    whatahel(user_id, profile_id, update, context)

        else:
            print("Error: query.data is not a string.")

    except Exception as e:
        print(f"Error processing like: {e}")


def get_username_from_id(bot, user_id):
    user = bot.get_chat(user_id)
    username = user.username
    return username

def whatahel(user_id, profile_id, update, context):
    try:
        context.bot.send_message(chat_id=profile_id, text=f"Кому-то понравилась твоя анкета!")
        display_profile_by_id(update, context, profile_id, user_id)
    except Exception as e:
        print(f"Error sending message to user {profile_id}: {e}")





def display_profile_by_id(update: Update, context: CallbackContext, chat_id, profile_id):
    user_data = get_user_data(profile_id)

    if not user_data:
        context.bot.send_message(chat_id, "Профиль не найден.")
        return

    profile_info = (
        f"Имя: {user_data['name']}\n"
        f"Возраст: {user_data['age']}\n"
        f"Пол: {user_data['gender']}\n"
        f"Город: {user_data['city']}\n"
        f"Биография: {user_data['bio']}\n"
    )
    photo_path = user_data.get('photo_path')
    if photo_path:
        try:
            photo_file = open(photo_path, 'rb')
            context.bot.send_photo(chat_id, photo_file, caption=profile_info)
        except FileNotFoundError:
            profile_info += "\nФото: Нет фото"
            context.bot.send_message(chat_id, profile_info)
    else:
        profile_info += "\nФото: Нет фото"
        context.bot.send_message(chat_id, profile_info)

    keyboard = [
        [InlineKeyboardButton("❤️ Понравилась анкета? Нажми ❤️", callback_data=f"like_{profile_id}")],
        [InlineKeyboardButton("⚠️ Жалоба", callback_data=f"report_{profile_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id, "Выберите действие:", reply_markup=reply_markup)








def check_like(user_id, liked_user_id):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM likes WHERE user_id=? AND liked_user_id=?", (user_id, liked_user_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def insert_like(user_id, liked_user_id):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO likes (user_id, liked_user_id) VALUES (?, ?)", (user_id, liked_user_id))
    conn.commit()
    conn.close()



def get_user_data(user_id):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        user_data = {
            'user_id': result[0],
            'name': result[1],
            'age': result[2],
            'gender': result[3],
            'city': result[4],
            'bio': result[5],
            'photo_path': result[6] if len(result) > 6 else None,
        }
        return user_data
    else:
        return None




def is_user_registered(user_id):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def delete_user_data(update: Update, context: CallbackContext):
    try:
        user_id = update.message.from_user.id
        conn = sqlite3.connect('dating_bot.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        conn.commit()
        print(f"User data deleted successfully for user_id: {user_id}")
        update.message.reply_text("Ваша анкета удалена. Вы можете зарегистрироваться заново с помощью /register.")
    except Exception as e:
        print(f"Error deleting user data: {e}")
    finally:
        conn.close()


def register(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Давайте начнем процесс регистрации.\nПожалуйста, укажите ваше имя:",
                              reply_markup=ReplyKeyboardRemove())
    context.user_data['registration_step'] = 1


def process_registration(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    registration_step = context.user_data.get('registration_step', 0)

    if registration_step == 1:
        context.user_data['name'] = update.message.text
        update.message.reply_text("Отлично! Теперь, пожалуйста, укажите ваш возраст:")
        context.user_data['registration_step'] = 2

    elif registration_step == 2:
        try:
            age = int(update.message.text)
            context.user_data['age'] = age

            keyboard = [
                [KeyboardButton("Мужчина")],
                [KeyboardButton("Женщина")],
            ]

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            update.message.reply_text("Понял! Теперь, укажите ваш пол (например, мужчина, женщина):", reply_markup=reply_markup)
            context.user_data['registration_step'] = 3
        except ValueError:
            update.message.reply_text("Некорректный возраст. Пожалуйста, введите корректное число.")

    elif registration_step == 3:
        context.user_data['gender'] = update.message.text.lower()
        reply_markup = ReplyKeyboardRemove()
        update.message.reply_text("Прекрасно! Теперь, пожалуйста, укажите ваш город:", reply_markup=reply_markup)
        context.user_data['registration_step'] = 4

    elif registration_step == 4:
        context.user_data['city'] = update.message.text
        update.message.reply_text("Почти готово! Пожалуйста, напишите небольшую биографию о себе:")
        context.user_data['registration_step'] = 5

    elif registration_step == 5:
        context.user_data['bio'] = update.message.text
        keyboard = [
            [KeyboardButton("Нет фото")],
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        update.message.reply_text("Отлично! Теперь отправьте ваше фото:",
                                  reply_markup=reply_markup)
        context.user_data['registration_step'] = 6


    elif registration_step == 6:
        if update.message.text == "Нет фото":
            # Handle case where user chooses not to provide a photo
            context.user_data['photo_path'] = ''
            save_user_to_database(user_id, context.user_data)
            context.user_data.clear()
            update.message.reply_text("Регистрация завершена! Теперь вы можете начать просмотр анкет с помощью /start.")
        elif update.message.photo:
            # Check if there are any photos in the message
            photo_file = update.message.photo[-1].get_file()
            os.makedirs("photos", exist_ok=True)
            photo_file.download(f"photos/{user_id}.jpg")
            context.user_data['photo_path'] = f"photos/{user_id}.jpg"
            save_user_to_database(user_id, context.user_data)
            context.user_data.clear()
            update.message.reply_text("Регистрация завершена! Теперь вы можете начать просмотр анкет с помощью /start.")
        else:
            update.message.reply_text("Вы не отправили фото. Пожалуйста, отправьте фото.")


def save_user_to_database(user_id, user_data):
    try:
        conn = sqlite3.connect('dating_bot.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, name, age, gender, city, bio, photo_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, user_data['name'], user_data['age'], user_data['gender'], user_data['city'], user_data['bio'],
              user_data.get('photo_path', '')))
        conn.commit()
        print(f"Debug: User data saved to the database. User ID: {user_id}")
    except Exception as e:
        print(f"Error saving user data to the database: {e}")
    finally:
        conn.close()


def browse(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    # Получение профилей из базы данных, исключая текущего пользователя
    profiles = get_all_profiles(user_id)

    if profiles:
        random_profile = random.choice(profiles)
        display_profile(update, context, random_profile)
    else:
        send_error_message(update)





from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def display_profile(update: Update, context: CallbackContext, profile):
    if not isinstance(profile, tuple):
        print(f"Error: Invalid profile format - {profile}")
        try:
            update.message.reply_text("Произошла ошибка при получении профиля. Пожалуйста, попробуйте еще раз.")
        except AttributeError:
            print("Error: Unable to reply to the user. update.message is None.")
        return

    user_id, name, age, gender, city, bio, photo_path = profile

    # Форматирование данных профиля для отображения
    profile_info = (
        f"Имя: {name}\n"
        f"Возраст: {age}\n"
        f"Пол: {gender}\n"
        f"Город: {city}\n"
        f"Биография: {bio}\n"
    )

    # Create InlineKeyboardMarkup with "Like" and "Report" buttons
    keyboard = [
        [InlineKeyboardButton("❤️ Понравилась анкета? Нажми ❤️", callback_data=f"like_{user_id}")],
        [InlineKeyboardButton("⚠️ Жалоба", callback_data=f"report_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if photo_path:
        try:
            photo_file = open(photo_path, 'rb')
            context.bot.send_photo(
                update.message.chat_id,
                photo_file,
                caption=profile_info,
                reply_markup=reply_markup
            )
        except FileNotFoundError:
            print(f"Error: Photo file not found - {photo_path}")
            try:
                update.message.reply_text("Произошла ошибка при получении профиля. Пожалуйста, попробуйте еще раз.")
            except AttributeError:
                print("Error: Unable to reply to the user. update.message is None.")
    else:
        profile_info += "Фото: Нет фото"
        try:
            update.message.reply_text(profile_info, reply_markup=reply_markup)
        except AttributeError:
            print("Error: Unable to reply to the user. update.message is None.")



def report_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    reported_user_id = int(query.data.split('_')[1])

    # Get the profile information of the reported user
    reported_user_data = get_user_data(reported_user_id)

    # Notify the admin user (ID: 728362175) about the complaint
    admin_user_id = 728362175
    notification_text = f"Поступила жалоба на пользователя {reported_user_id}.\n\n" \
                        f"Имя: {reported_user_data['name']}\n" \
                        f"Возраст: {reported_user_data['age']}\n" \
                        f"Пол: {reported_user_data['gender']}\n" \
                        f"Город: {reported_user_data['city']}\n" \
                        f"Биография: {reported_user_data['bio']}\n"

    keyboard = [
        [InlineKeyboardButton("Пропустить", callback_data=f"skip_report_{reported_user_id}")],
        [InlineKeyboardButton("Удалить профиль", callback_data=f"delete_profile_{reported_user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=admin_user_id, text=notification_text, reply_markup=reply_markup)

    # Inform the user who reported about the action
    context.bot.send_message(chat_id=query.from_user.id, text="Ваша жалоба была отправлена администратору.")


def skip_report(update: Update, context: CallbackContext):
    query = update.callback_query
    reported_user_id = int(query.data.split('_')[2])

    # Extract the user ID from the callback query
    user_id = query.from_user.id if query.from_user else None

    if user_id:
        # Perform the action to skip the report (call the show_menu function)
        show_menu(update, context)
    else:
        # Log an error or handle the situation when user ID is not available
        print("Error: User ID not available in the callback query.")





def delete_profile(update: Update, context: CallbackContext):
    query = update.callback_query
    reported_user_id = int(query.data.split('_')[2])

    # Perform the action to delete the profile of the reported user
    # Implement the necessary logic to delete the profile from the database
    delete_user_data_by_id(reported_user_id)

    # Inform the admin about the deletion
    context.bot.send_message(chat_id=query.from_user.id, text=f"Профиль пользователя {reported_user_id} удален.")

    # Inform the reported user about the deletion
    context.bot.send_message(chat_id=reported_user_id, text="Ваш профиль был удален по жалобе.")


def delete_user_data_by_id(user_id):
    # Implement the logic to delete the user data from the database by user ID
    try:
        conn = sqlite3.connect('dating_bot.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        conn.commit()
        print(f"User data deleted successfully for user_id: {user_id}")
    except Exception as e:
        print(f"Error deleting user data: {e}")
    finally:
        conn.close()

def send_error_message(update: Update):
    if update.message:
        update.message.reply_text("Ошибка при получении пользователя. Пожалуйста, попробуйте еще раз.")
    else:
        # Log the error or handle it accordingly
        print("Error: update.message is None.")


def get_all_profiles(current_user_id):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, age, gender, city, bio, photo_path FROM users WHERE user_id != ?", (current_user_id,))
    profiles = cursor.fetchall()
    conn.close()
    return profiles



def show_keyboard(update: Update, context: CallbackContext) -> None:
    # Отображение клавиатуры с тремя кнопками и кнопкой "Меню"
    keyboard = [
        [KeyboardButton("Дальше")],
        [KeyboardButton("Меню")],
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    # Provide a non-empty text parameter when sending the message
    context.bot.send_message(update.message.chat_id, text="Выберите нужный вариант:", reply_markup=reply_markup)



def show_menu(update: Update, context: CallbackContext) -> None:
    # Запуск функции start при нажатии кнопки "Меню"
    start(update, context)


def format_profile_text(profile):
    # Форматирование данных профиля для отображения
    if profile:
        user_id, name, age, gender, city, bio, photo_path = profile
        profile_info = (
            f"Имя: {name}\n"
            f"Возраст: {age}\n"
            f"Пол: {gender}\n"
            f"Город: {city}\n"
            f"Биография: {bio}\n"
        )
        if photo_path:
            try:
                photo_file = open(photo_path, 'rb')
                return profile_info, photo_file
            except FileNotFoundError:
                return "Профиль не найден. Фото не загружено.", None
        else:
            profile_info += "Фото: Нет фото"
            return profile_info, None
    else:
        return "Профиль не найден.", None


def delete_all_likes(update, context):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM likes")
    update.message.reply_text("Все ваши лайки были успешно удалены.")
    conn.commit()
    conn.close()

ADMIN_USER_ID = 728362175

def send_message_to_all(update: Update, context: CallbackContext) -> None:
    # Check if the user who triggered the command is the admin
    if update.message.from_user.id != ADMIN_USER_ID:
        update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    try:
        # Fetch all user IDs from the database
        conn = sqlite3.connect('dating_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        user_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Send the message to each user
        message_text = " ".join(context.args)  # Extract the message text from the command arguments
        for user_id in user_ids:
            try:
                context.bot.send_message(chat_id=user_id, text=message_text)
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")

        update.message.reply_text(f"Сообщение успешно отправлено всем пользователям: {message_text}")

    except Exception as e:
        update.message.reply_text(f"Произошла ошибка при отправке сообщения: {e}")



def main() -> None:
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("register", register))
    dp.add_handler(CommandHandler("keyboard", show_keyboard))
    dp.add_handler(CommandHandler("delete_all_likes", delete_all_likes))
    dp.add_handler(MessageHandler(Filters.regex(r'^Меню$'), show_menu))
    dp.add_handler(MessageHandler(Filters.regex(r'^Моя анкета$'), my_profile))
    dp.add_handler(MessageHandler(Filters.regex(r'^Удалить анкету$'), delete_user_data))
    dp.add_handler(MessageHandler(Filters.regex(r'^Начать поиск$'), start_browsing))
    dp.add_handler(MessageHandler(Filters.regex(r'^Дальше$'), start_browsing))
    dp.add_handler(MessageHandler(Filters.regex(r'^Информация$'), info))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, process_registration))
    dp.add_handler(MessageHandler(Filters.photo, process_registration))
    dp.remove_handler(dp.handlers[0])  # Assuming CallbackQueryHandler is the first handler
    dp.add_handler(CommandHandler("browse", browse))
    dp.add_handler(CallbackQueryHandler(like, pattern=r'^like_'))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, process_text_message))
    dp.add_handler(CallbackQueryHandler(report_handler, pattern=r'^report_'))
    dp.add_handler(CallbackQueryHandler(skip_report, pattern=r'^skip_report_'))
    dp.add_handler(CallbackQueryHandler(delete_profile, pattern=r'^delete_profile_'))
    dp.add_handler(CommandHandler('send', send_message_to_all, pass_args=True))
    info_handler = CommandHandler('info', info)
    dp.add_handler(info_handler)


    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()