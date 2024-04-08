import types

import telebot
import psycopg2

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
        # Получаем user_id из контекста

        # Обновляем номер телефона пользователя в записи с указанным user_id
        cursor.execute("UPDATE Users SET phone_number = %s WHERE user_id = %s", (phone_number, user_id))
        conn.commit()
        bot.send_message(message.chat.id, "Номер телефона успешно сохранен! Теперь вы можете выбрать услугу.")
        # Здесь мы можем перейти к следующему шагу нашего сценария
        # Например, предоставить пользователю выбор услуги
    except Exception as e:
        bot.send_message(message.chat.id,
                         "Произошла ошибка при сохранении номера телефона. Попробуйте еще раз или обратитесь к администратору.")
        print(e)





# Запускаем бота
bot.polling(none_stop=True)

# Закрываем соединение с базой данных при завершении работы бота
cursor.close()
conn.close()
