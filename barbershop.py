
import datetime
import telebot
import psycopg2
from telebot import types






conn = psycopg2.connect(
    dbname="barbershop",
    user="postgres",
    password="200920055",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()



TOKEN = '6663688129:AAHbceSjOa5oDyoKb5rKtWY8wZn17wn6jdE'


bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    register_button = types.KeyboardButton("Зарегистрироваться")
    admin_login_button = types.KeyboardButton("Вход для администратора")
    keyboard.add(register_button, admin_login_button)

    bot.send_message(message.chat.id, "Добро пожаловать в бота для записи в барбершоп! Выберите действие:", reply_markup=keyboard)
    bot.send_photo(message.chat.id,
                   "https://sun9-53.userapi.com/impg/B-mxiX34XR0AwuBnm0OGEYGzdUo40in3OKsK_Q/suHVdQXxzZY.jpg?size=598x574&quality=95&sign=a0a187316e8f42bfb1f3f21037cb6fe9&type=album")


@bot.message_handler(func=lambda message: message.text == "Вход для администратора")
def admin_login(message):
    bot.send_message(message.chat.id, "Введите пароль для администратора:")
    bot.register_next_step_handler(message, check_admin_password)


def check_admin_password(message):
    admin_password = "200920055"
    if message.text == admin_password:
        bot.send_message(message.chat.id, "Вы успешно вошли как администратор.")
        show_admin_menu(message)
    else:
        bot.send_message(message.chat.id, "Неверный пароль. Попробуйте снова.")
        admin_login(message)


def show_admin_menu(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    view_feedback_button = types.KeyboardButton("Просмотреть все записи")
    view_appointments_button = types.KeyboardButton("Удалить запись")
    delete_barbers = types.KeyboardButton("Удалить барбера")
    user_mode_btn = types.KeyboardButton("Войти как пользователь")
    keyboard.add(view_feedback_button, view_appointments_button,delete_barbers, user_mode_btn)
    bot.send_message(message.chat.id, "Административное меню:", reply_markup=keyboard)



@bot.message_handler(func=lambda message: message.text == "Удалить барбера")
def delete_barber_prompt(message):
    cursor.execute("SELECT name FROM barbers")
    barbers = cursor.fetchall()
    if barbers:
        barber_list = "\n".join([barber[0] for barber in barbers]) #barber[0] нужен для распаковки кортежа
        bot.send_message(message.chat.id, f"Список барберов:\n{barber_list}\nВведите имя барбера для удаления:")
        bot.register_next_step_handler(message, delete_barber)
    else:
        bot.send_message(message.chat.id, "Список барберов пуст.")

def delete_barber(message):
    barber_name = message.text.strip()
    cursor.execute("SELECT * FROM barbers WHERE name = %s", (barber_name,))
    barber = cursor.fetchone()
    if barber:
        cursor.execute("DELETE FROM barbers WHERE name = %s", (barber_name,))
        conn.commit()
        bot.send_message(message.chat.id, f"Барбер '{barber_name}' успешно удален.")
    else:
        bot.send_message(message.chat.id, f"Барбер с именем '{barber_name}' не найден.")


@bot.message_handler(func=lambda message: message.text == "Войти как пользователь")
def user_login(message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    if user:
        back_to_main_menu(message)
    else:
        start_message(message)



@bot.message_handler(func=lambda message: message.text == "Просмотреть все записи")
def view_appointments(message):
    cursor.execute("SELECT user_id, service_name, appointment_date, appointment_time, barber_name FROM appointments")
    appointments = cursor.fetchall()

    if appointments:
        for appointment in appointments:
            user_id, service_name, appointment_date, appointment_time, barber_name = appointment
            appointment_info = (f"Пользователь ID: {user_id}\n"
                                f"Услуга: {service_name}\n"
                                f"Дата: {appointment_date}\n"
                                f"Время: {appointment_time}\n"
                                f"Барбер: {barber_name}")
            bot.send_message(message.chat.id, appointment_info)
    else:
        bot.send_message(message.chat.id, "Записей пока нет.")


@bot.message_handler(func=lambda message: message.text == "Удалить запись")
def delete_appointment_prompt(message):
    bot.send_message(message.chat.id, "Введите ID пользователя, для которого нужно удалить запись:")
    bot.register_next_step_handler(message, delete_appointment)


def delete_appointment(message):
    try:
        user_id = int(message.text)
        cursor.execute("SELECT * FROM appointments WHERE user_id = %s", (user_id,))
        appointment = cursor.fetchone()

        if appointment:
            cursor.execute("UPDATE appointments SET barber_name = NULL, service_name = NULL, appointment_date = NULL, appointment_time = NULL WHERE user_id = %s",(user_id,))
            conn.commit()
            bot.send_message(message.chat.id, f"Запись для пользователя с ID {user_id} успешно удалена.")
        else:
            bot.send_message(message.chat.id, f"Запись для пользователя с ID {user_id} не найдена.")

    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат ID. Попробуйте снова.")
        delete_appointment_prompt(message)



@bot.message_handler(func=lambda message: message.text == "Зарегистрироваться")
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Я бот парикмахерской Fedulov's Barbershop. Хочешь сделаем из тебя брутального мужчину ;) ? Тогда ответь, как тебя зовут?")
    user_id = message.from_user.id
    bot.register_next_step_handler(message, save_name, user_id)



def save_name(message, user_id):

    if message.text is None:
        bot.send_message(message.chat.id, "Пожалуйста, введите имя в текстовом формате.")
        bot.register_next_step_handler(message, save_name, user_id)
        return


    name = message.text.strip()



    if not name.isalpha():
        bot.send_message(message.chat.id, "Имя не должно содержать цифр или пробелов. Попробуйте еще раз.")
        bot.register_next_step_handler(message, save_name, user_id)
        return

    try:

        cursor.execute("INSERT INTO Users (user_id, username) VALUES (%s, %s)", (user_id, name))
        cursor.execute("INSERT INTO appointments (user_id) VALUES (%s)", (user_id,))
        conn.commit()
        bot.send_message(message.chat.id, "Имя успешно сохранено! Теперь введите свой номер телефона:")
        # Регистрируем следующий шаг для сохранения номера телефона
        bot.register_next_step_handler(message, save_phone, user_id)
    except Exception as e:
        bot.send_message(message.chat.id,
                         "Произошла ошибкa: У тебя уже есть учетная запись!")
        print(e)




def save_phone(message, user_id):

    if message.text is None:
        bot.send_message(message.chat.id, "Пожалуйста, введите номер в текстовом формате.")
        bot.register_next_step_handler(message, save_phone, user_id)
        return


    phone_number = message.text.strip()


    if  not phone_number.replace('+', '').isdigit():
        bot.send_message(message.chat.id, "Номер телефона может содержать только цифры и знак +. Пожалуйста, введи корректный номер!")
        bot.register_next_step_handler(message, save_phone, user_id)
        return

    if len(phone_number) > 12:
        bot.send_message(message.chat.id, "Слишком длинный номер телефона. Пожалуйста, введите корректный номер.")
        bot.register_next_step_handler(message, save_phone, user_id)
        return
    if len(phone_number) < 5:
        bot.send_message(message.chat.id, "Слишком короткий номер телефона. Пожалуйста, введите корректный номер.")
        bot.register_next_step_handler(message, save_phone, user_id)
        return

    try:

        cursor.execute("UPDATE Users SET phone_number = %s WHERE user_id = %s", (phone_number, user_id))
        conn.commit()
        bot.send_message(message.chat.id, "Номер телефона успешно сохранен! Супер, теперь вы можете выбрать услугу.")
        bot.send_photo(message.chat.id, "https://sun9-32.userapi.com/impg/rlTUzEXXe45ZQS0zKq6Wak0V5Sy4n3tLyZOfwQ/Vk9yJCQtDaY.jpg?size=1980x1372&quality=95&sign=50142002c0bbc1f4bc00cf9c9132f040&type=album")
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)


        services_button = types.KeyboardButton("Услуги")
        barbers_button = types.KeyboardButton("Барберы")
        my_orders_button = types.KeyboardButton("Моя запись")

        keyboard.add(services_button, barbers_button, my_orders_button)

        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)

    except Exception as e:
        bot.send_message(message.chat.id,
                         "Произошла ошибка при сохранении номера телефона. Попробуйте еще раз или обратитесь к администратору.")
        print(e)


@bot.message_handler(func=lambda message: message.text == 'Барберы')
def send_barbers_info(message):
    try:
        # Выполняем SQL-запрос для извлечения информации о барберах из таблицы "Barbers"
        cursor.execute("SELECT name, phone_number, experience_year, age_year FROM Barbers")
        barbers_info = cursor.fetchall()

        if barbers_info:
            response = "Список барберов:\n"
            for barber in barbers_info:
                name, phone_number, experience, age = barber
                response += f"Имя: {name}\nНомер телефона: {phone_number}\nВозраст: {age}\nСтаж работы: {experience} лет\n\n"
            bot.send_message(message.chat.id, response)

    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")
        print(e)



@bot.message_handler(func=lambda message: message.text == 'Услуги')
def send_services(message):
    try:
        
        cursor.execute("SELECT name FROM Services")
        services = cursor.fetchall()

        
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

       
        for service in services:
            service_name = service[0]  
            keyboard.add(types.KeyboardButton(service_name))

       
        bot.send_message(message.chat.id, "Выберите услугу:", reply_markup=keyboard)

    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")
        print(e)



@bot.message_handler(func=lambda message: message.text in ["Бритье", "Окрашивание", "Укладка", "Стрижка бороды","Стрижка"])
def send_service_info(message):
    try:
        selected_service = message.text
        user_id = message.from_user.id


        cursor.execute("UPDATE appointments SET service_name = %s WHERE user_id = %s", (selected_service, user_id))
        conn.commit()
        cursor.execute("SELECT description, price FROM Services WHERE name = %s", (selected_service,))
        service_info = cursor.fetchone()

        if service_info:
            description, price = service_info

            service_text = f"Название услуги: {selected_service}\nОписание: {description}\nЦена: {price} руб."

            keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            keyboard.add(types.KeyboardButton("Назад"), types.KeyboardButton("Выбрать"))

            bot.send_message(message.chat.id, service_text, reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "Информация о выбранной услуге недоступна.")

    except Exception as e:
        bot.send_message(message.chat.id, "Выбери услугу, нажав на кнопку.")
        send_services(message)
        print(e)



@bot.message_handler(func=lambda message: message.text == 'Назад')
def back_to_main_menu(message):
    try:
        
        keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        keyboard.add(types.KeyboardButton("Услуги"), types.KeyboardButton("Барберы"), types.KeyboardButton("Моя запись"))
       
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")
        print(e)


@bot.message_handler(func=lambda message: message.text == 'Выбрать')
def select_barbers(message):
    try:

        cursor.execute("SELECT name FROM Barbers")
        barbers = cursor.fetchall()

        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

        for barber in barbers:
            barber_name = barber[0]
            keyboard.add(types.KeyboardButton(barber_name))

        bot.send_message(message.chat.id, "Выбери барбера:", reply_markup=keyboard)

    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")
        print(e)

@bot.message_handler(func=lambda message: message.text in ["Иван Иванов", "Петр Петров", "Александр Сидоров", "Дмитрий Попов","Андрей Васильев","Алексей Алексеев"]) # Замените имена на реальные имена барберов
def handle_selected_barber(message):
    try:
        selected_barber = message.text
        user_id = message.from_user.id

        cursor.execute("UPDATE appointments SET barber_name = %s WHERE user_id = %s", (selected_barber, user_id))
        conn.commit()

        request_date(message)


    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}. Попробуйте позже.")


def request_date(message):

    bot.send_message(message.chat.id, "Введите дату в формате DD.MM.YYYY:")
    bot.register_next_step_handler(message, save_date)

def save_date(message):
    try:

        if message.text is None:
            bot.send_message(message.chat.id, "Пожалуйста, введите дату в текстовом формате.")
            request_date(message)
            return

        selected_date = datetime.datetime.strptime(message.text, "%d.%m.%Y")


        today = datetime.datetime.today()
        if selected_date < today:
            bot.send_message(message.chat.id, "Выбранная дата не может быть раньше сегодняшней.")
            request_date(message)
            return


        three_months_later = today + datetime.timedelta(days=90)
        if selected_date > three_months_later:
            bot.send_message(message.chat.id, "Запись доступна только на ближайшие три месяца!")
            request_date(message)
            return


        user_id = message.from_user.id
        cursor.execute("UPDATE appointments SET appointment_date = %s WHERE user_id = %s", (selected_date, user_id))
        conn.commit()
        bot.send_message(message.chat.id, f"Вы выбрали дату: {selected_date.strftime('%d.%m.%Y')}")
        select_time(message)

    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты. Введите дату в формате DD.MM.YYYY.")
        request_date(message)



def select_time(message):
    try:


        keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)


        keyboard.add(types.KeyboardButton("10:00"), types.KeyboardButton("11:00"))
        keyboard.add(types.KeyboardButton("12:00"), types.KeyboardButton("14:00"))
        keyboard.add(types.KeyboardButton("15:00"), types.KeyboardButton("16:00"))


        bot.send_message(message.chat.id, f"Выберите время:", reply_markup=keyboard)


    except:
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")


@bot.message_handler(func=lambda message: message.text in ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00"])
def handle_selected_time(message):
    try:
        selected_time = message.text
        user_id = message.from_user.id

        cursor.execute("UPDATE appointments SET appointment_time = %s WHERE user_id = %s", (selected_time, user_id))
        conn.commit()

        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

        my_order = types.KeyboardButton("Моя запись")
        change_order = types.KeyboardButton("Удалить мою запись")
        admin = types.KeyboardButton("Вход для администратора")

        keyboard.add(my_order, change_order, admin)
        bot.send_message(message.chat.id, f"Вы выбрали время: {selected_time}. Ваша заявка успешно создана! Вам позвонит менеджер для подтверждения.", reply_markup=keyboard)

    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}. Попробуйте позже.")



@bot.message_handler(func=lambda message: message.text == "Удалить мою запись")
def confirm_overwrite(message):
    try:
        # Создаем клавиатуру с кнопками "Да" и "Нет"
        keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        yes_button = types.KeyboardButton("Да")
        no_button = types.KeyboardButton("Нет")
        keyboard.add(yes_button, no_button)

        # Отправляем сообщение с вопросом о подтверждении
        bot.send_message(message.chat.id, "Точно ли вы хотите удалить запись? ", reply_markup=keyboard)

        # Регистрируем следующий шаг для обработки ответа пользователя
        bot.register_next_step_handler(message, process_overwrite_confirmation)

    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка.")


def process_overwrite_confirmation(message):
    try:

        if message.text.lower() == "да":
            user_id = message.from_user.id
            cursor.execute("UPDATE appointments SET barber_name = NULL, service_name = NULL, appointment_date = NULL, appointment_time = NULL WHERE user_id = %s",(user_id,))
            conn.commit()
            bot.send_message(message.chat.id, "Прошлая запись успешно удалена!")
            back_to_main_menu(message)


        elif message.text.lower() == "нет":
            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)


            my_order = types.KeyboardButton("Моя запись")
            change_order = types.KeyboardButton("Удалить мою запись")
            admin = types.KeyboardButton("Вход для администратора")

            keyboard.add(my_order, change_order, admin)
            bot.send_message(message.chat.id,f"Не опаздывайте на свою запись, мы вас ждем ;)", reply_markup=keyboard)



        else:
            bot.send_message(message.chat.id, "Я не могу понять ваш ответ. Пожалуйста, введите 'Да' или 'Нет'.")
            confirm_overwrite(message)

    except Exception as e:
        bot.send_message(message.chat.id, f"Я не могу понять ваш ответ. Пожалуйста, введите 'Да' или 'Нет'.")
        confirm_overwrite(message)



@bot.message_handler(func=lambda message: message.text == "Моя запись")
def show_appointment(message):
    try:
        user_id = message.from_user.id

        cursor.execute("SELECT service_name, appointment_date, appointment_time, barber_name FROM appointments WHERE user_id = %s", (user_id,))
        appointment = cursor.fetchone()

        if appointment:
            service_name, appointment_date, appointment_time, barber_name = appointment

            appointment_info = (f"Ваша запись:\n"
                                f"Услуга: {service_name}\n"
                                f"Дата: {appointment_date}\n"
                                f"Время: {appointment_time}\n"
                                f"Барбер: {barber_name}")
            bot.send_message(message.chat.id, appointment_info)
        else:
            bot.send_message(message.chat.id, "У вас нет записи.")

    except Exception as e:
        bot.send_message(message.chat.id, f"У вас нет активной записи.")




bot.polling(none_stop=True)


cursor.close()
conn.close()
