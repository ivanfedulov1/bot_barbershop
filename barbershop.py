
import telebot
import psycopg2
from telebot import types

# Устанавливаем соединение с базой данных PostgreSQL
conn = psycopg2.connect(
    dbname="barbershop",
    user="postgres",
    password="200920055",
    host="localhost",
    port="5432"
)

# Создаем курсор для выполнения SQL-запросов
cursor = conn.cursor()

# Указываем токен вашего бота
TOKEN = '6663688129:AAHbceSjOa5oDyoKb5rKtWY8wZn17wn6jdE'

# Создаем объект бота
bot = telebot.TeleBot(TOKEN)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Я бот парикмахерской Fedulov's Barbershop. Хочешь сделаем из тебя брутального мужчину ;) ? Тогда ответь, как тебя зовут?")
    bot.register_next_step_handler(message, save_name)


# Функция для сохранения имени пользователя
def save_name(message):
    name = message.text.strip()

    # Проверка валидности имени пользователя
    if not name.isalpha():
        bot.send_message(message.chat.id, "Имя не должно содержать цифр. Попробуйте еще раз.")
        bot.register_next_step_handler(message, save_name)
        return

    try:
        # Добавляем имя пользователя в созданную запись
        cursor.execute("INSERT INTO Users (username) VALUES (%s) RETURNING user_id", (name,))
        user_id = cursor.fetchone()[0]
        conn.commit()
        bot.send_message(message.chat.id, "Имя успешно сохранено! Теперь введите свой номер телефона:")
        # Регистрируем следующий шаг для сохранения номера телефона
        bot.register_next_step_handler(message, save_phone, user_id)
    except Exception as e:
        bot.send_message(message.chat.id,
                         "Произошла ошибка при сохранении имени. Попробуйте еще раз или обратитесь к администратору.")
        print(e)



# Функция для сохранения номера телефона пользователя
def save_phone(message, user_id):
    phone_number = message.text.strip()

    # Проверяем, состоит ли введенный номер только из цифр и символа "+"
    if not phone_number.replace('+', '').isdigit():
        bot.send_message(message.chat.id, "Дружок, номер телефона может содержать только цифры и знак +. Пожалуйста, введи корректный номер!")
        bot.register_next_step_handler(message, save_phone, user_id)
        return

    if len(phone_number) > 12:
        bot.send_message(message.chat.id, "Слишком длинный номер телефона. Пожалуйста, введите корректный номер.")
        bot.register_next_step_handler(message, save_phone, user_id)
        return

    try:

        # Обновляем номер телефона пользователя в записи с указанным user_id
        cursor.execute("UPDATE Users SET phone_number = %s WHERE user_id = %s", (phone_number, user_id))
        conn.commit()
        bot.send_message(message.chat.id, "Номер телефона успешно сохранен! Супер, теперь вы можете выбрать услугу.")

        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    # Добавляем кнопки в меню
        services_button = types.KeyboardButton("Услуги")
        barbers_button = types.KeyboardButton("Барберы")
        my_orders_button = types.KeyboardButton("Мои заказы")
    # Добавляем кнопки к меню
        keyboard.add(services_button, barbers_button, my_orders_button)
    # Отправляем сообщение с кнопочным меню
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)

    except Exception as e:
        bot.send_message(message.chat.id,
                         "Произошла ошибка при сохранении номера телефона. Попробуйте еще раз или обратитесь к администратору.")
        print(e)




# Обработчик для кнопки "Услуги"
@bot.message_handler(func=lambda message: message.text == 'Услуги')
def send_services(message):
    try:
        # Выполнение SQL-запроса для извлечения названий услуг из таблицы "Services"
        cursor.execute("SELECT name FROM Services")
        services = cursor.fetchall()

        # Создание клавиатуры для выбора услуг
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

        # Добавление кнопок для каждой услуги
        for service in services:
            service_name = service[0]  # Получаем название услуги из кортежа
            keyboard.add(types.KeyboardButton(service_name))

        # Отправка сообщения с клавиатурой пользователю
        bot.send_message(message.chat.id, "Выберите услугу:", reply_markup=keyboard)

    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")
        print(e)


# Обработчик для кнопок с названием услуги
@bot.message_handler(func=lambda message: is_service(message.text))
def send_service_info(message):
    try:
        selected_service = message.text

        # Выполнение SQL-запроса для получения описания и цены выбранной услуги
        cursor.execute("SELECT description, price FROM Services WHERE name = %s", (selected_service,))
        service_info = cursor.fetchone()  # Получаем описание и цену услуги

        if service_info:
            description, price = service_info
            # Формируем текст с описанием и ценой услуги
            service_text = f"Название услуги: {selected_service}\nОписание: {description}\nЦена: {price} руб."
            # Создаем клавиатуру для выбора дальнейших действий
            keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            keyboard.add(types.KeyboardButton("Назад"), types.KeyboardButton("Выбрать"))
            # Отправляем сообщение с описанием услуги и клавиатурой пользователю
            bot.send_message(message.chat.id, service_text, reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "Информация о выбранной услуге недоступна.")

    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")
        print(e)

# Функция для проверки, является ли текст сообщения названием услуги
def is_service(text):
    try:
        # Выполнение SQL-запроса для получения списка доступных услуг
        cursor.execute("SELECT name FROM Services")
        available_services = cursor.fetchall()  # Получаем список названий услуг

        # Проверяем, есть ли введенный текст в списке названий услуг
        return text in [service[0] for service in available_services]
    except Exception as e:
        print("Ошибка при проверке услуги:", e)
        return False

# Обработчик для кнопки "Назад"
@bot.message_handler(func=lambda message: message.text == 'Назад')
def back_to_main_menu(message):
    try:
        # Создаем клавиатуру для основного меню
        keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        keyboard.add(types.KeyboardButton("Услуги"), types.KeyboardButton("Барберы"), types.KeyboardButton("Мои заказы"))
        # Отправляем сообщение с основным меню пользователю
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")
        print(e)


# Запускаем бота
bot.polling(none_stop=True)

# Закрываем соединение с базой данных при завершении работы бота
cursor.close()
conn.close()