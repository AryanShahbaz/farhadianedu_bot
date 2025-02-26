import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, Message, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import re
from config import TOKEN, GROUP_ID
import datetime
from datetime import datetime

# TOKEN = "7743113134:AAGhA2HVYoGKgxdf1mbJqoR46sTqXXJMSCs"
# GROUP_ID = -1002369534993
TOKEN = "7743113134:AAGhA2HVYoGKgxdf1mbJqoR46sTqXXJMSCs"
GROUP_ID = -1002369534993


bot = telebot.TeleBot(TOKEN)

now= datetime.now()

print("Bot is Running....")
print("Time : "+ now.strftime("%Y-%m-%d %H:%M:%S"))

# دیتابیس
def init_db():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
                        user_id INTEGER PRIMARY KEY, 
                        name TEXT, 
                        age INTEGER, 
                        phone TEXT,
                        grade TEXT, 
                        major TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        subject TEXT,
                        question TEXT,
                        status TEXT DEFAULT 'پاسخ نداده',
                        FOREIGN KEY(user_id) REFERENCES students(user_id))''')
    conn.commit()
    conn.close()

init_db()

def save_student(user_id, name, age, phone, grade, major):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO students (user_id, name, age, phone, grade, major) VALUES (?, ?, ?, ?, ?, ?)", 
                   (user_id, name, age, phone, grade, major))
    conn.commit()
    conn.close()

def get_student(user_id):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE user_id = ?", (user_id,))
    student = cursor.fetchone()
    conn.close()
    return student


def validate_phone(phone):
    pattern = r"^\+?\d{10,15}$"
    return re.match(pattern, phone)

@bot.message_handler(commands=["start"])
def start(message: Message):
    user_id = message.chat.id
    student = get_student(user_id)
    if student:
        send_main_menu(user_id)
    else:
        bot.send_message(user_id, "سلام! لطفاً نام و نام خانوادگی خود را وارد کنید:")
        bot.register_next_step_handler(message, process_name)

def process_name(message: Message):
    user_id = message.chat.id
    name = message.text
    bot.send_message(user_id, "لطفاً سن خود را وارد کنید:")
    bot.register_next_step_handler(message, process_age, name)

def process_age(message: Message, name):
    user_id = message.chat.id
    try:
        age = int(message.text)
        bot.send_message(user_id, "لطفاً شماره موبایل خود را وارد کنید:")
        bot.register_next_step_handler(message, process_phone, name, age)
    except ValueError:
        bot.send_message(user_id, "❌ لطفاً سن خود را به صورت عددی وارد کنید.")
        bot.register_next_step_handler(message, process_age, name)

def process_phone(message: Message, name, age):
    user_id = message.chat.id
    phone = message.text
    if not validate_phone(phone):
        bot.send_message(user_id, "❌ شماره موبایل وارد شده معتبر نیست. لطفاً دوباره تلاش کنید.")
        bot.register_next_step_handler(message, process_phone, name, age)
        return
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("دهم", "یازدهم", "دوازدهم", "پشت کنکوری")
    bot.send_message(user_id, "پایه تحصیلی خود را انتخاب کنید:", reply_markup=markup)
    bot.register_next_step_handler(message, process_grade, name, age, phone)

VALID_GRADES = ["دهم", "یازدهم", "دوازدهم", "پشت کنکوری"]
VALID_MAJORS = ["ریاضی", "تجربی", "انسانی"]

def process_grade(message: Message, name, age, phone):
    grade = message.text
    if grade not in VALID_GRADES:
        bot.send_message(message.chat.id, "❌ لطفاً یکی از گزینه‌های صحیح را انتخاب کنید.")
        bot.register_next_step_handler(message, process_grade, name, age, phone)
        return

    user_id = message.chat.id
    grade = message.text
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("ریاضی", "تجربی", "انسانی")
    bot.send_message(user_id, "رشته تحصیلی خود را انتخاب کنید:", reply_markup=markup)
    bot.register_next_step_handler(message, process_major, name, age, phone, grade)

def process_major(message: Message, name, age, phone, grade):
    user_id = message.chat.id
    major = message.text
    save_student(user_id, name, age, phone, grade, major)
    bot.send_message(user_id, "ثبت نام شما با موفقیت انجام شد! 🎉")
    send_main_menu(user_id)

def send_main_menu(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("ارسال سوال")
    bot.send_message(user_id, "لطفاً گزینه موردنظر خود را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "ارسال سوال")
def ask_question(message: Message):
    user_id = message.chat.id
    student = get_student(user_id)
    if not student:
        bot.send_message(user_id, "ابتدا باید ثبت نام کنید.")
        return
    
    key = (student[4], student[5])
    
    subjects = {
        ("دهم", "تجربی"): ["ریاضی 1", "فیزیک 1", "شیمی 1", "زیست شناسی 1"],
        ("دهم", "ریاضی"): ["ریاضی 1", "فیزیک 1", "شیمی 1", "هندسه 1"],
        ("دهم", "انسانی"): ["فارسی 1", "عربی 1", "دین و زندگی 1", "زبان انگلیسی 1", "ریاضی و آمار 1", "علوم و فنون ادبی 1", "تاریخ 1", "جغرافیا 1", "جامعه شناسی 1", "منطق 1", "اقتصاد"],
        ("یازدهم", "تجربی"): ["ریاضی 2", "فیزیک 2", "شیمی 2", "زیست شناسی 2", "زمین شناسی"],
        ("یازدهم", "ریاضی"): ["حسابان 1", "هندسه 2", "شیمی 2", "فیزیک 2", "آمار و احتمال"],
        ("یازدهم", "انسانی"): ["فارسی 2", "دین و زندگی 2", "عربی 2", "زبان انگلیسی 2", "ریاضی و آمار 2", "علوم و فنون ادبی 2", "تاریخ 2", "جغرافیا 2", "جامعه شناسی 2", "فلسفه 1", "روان شناسی"],
        ("دوازدهم", "تجربی"): ["ریاضی", "فیزیک", "شیمی", "زیست شناسی"],
        ("دوازدهم", "ریاضی"): ["حسابان", "شیمی", "فیزیک", "ریاضیات گسسته"],
        ("دوازدهم", "انسانی"): ["ریاضی و آمار ۳", "علوم و فنون ادبی ۳", "تاریخ ۳", "جغرافیا ۳", "جامعه‌شناسی ۳", "فلسفه ۲", "منطق ۲", "فارسی 3", "عربی 3", "دین و زندگی 3", "زبان انگلیسی 3"]
    }

    subject_list = subjects.get(key, [])

    if not subject_list:
        bot.send_message(user_id, "متاسفانه دروس شما پیدا نشدند. لطفاً مجدداً ثبت‌نام کنید.")
        return

    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for subject in subject_list:
        markup.add(subject)
    
    bot.send_message(user_id, "درس مورد نظر خود را انتخاب کنید:", reply_markup=markup)
    bot.register_next_step_handler(message, process_subject)

def process_subject(message: Message):
    user_id = message.chat.id
    subject = message.text
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بازگشت به منو قبل")
    bot.send_message(user_id, f"شما درس {subject} را انتخاب کردید. حالا مشکل خود را وارد کنید.", reply_markup=markup)
    bot.register_next_step_handler(message, process_problem, user_id, subject)

def process_problem(message: Message, user_id, subject):
    problem = message.text
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("نمیدونم از کجا شروع کنم", "فرمول‌ها رو بلد نیستم", "روش حل رو متوجه نمیشم") 
    markup.add("حل پاسخنامه رو متوجه نمیشم", "منظور سوال رو نمیفهمم", "سایر", "🔙 بازگشت به منو قبل")
    bot.send_message(user_id, "مشکل شما در حل این سوال چیه؟", reply_markup=markup)
    bot.register_next_step_handler(message, process_custom_problem, user_id, subject, problem)

def process_custom_problem(message: Message, user_id, subject, question_text):
    problem = message.text
    if problem == "سایر":
        bot.send_message(user_id, "لطفاً مشکل خود را به صورت دقیق‌تر وارد کنید.")
        bot.register_next_step_handler(message, get_problem_description, user_id, subject, question_text)
    else:
        bot.send_message(user_id, "لطفاً فایل پی دی اف یا عکس ارسال کنید.")
        bot.register_next_step_handler(message, process_file, user_id, subject, question_text, problem)

def get_problem_description(message: Message, user_id, subject, question_text):
    problem = message.text
    bot.send_message(user_id, "لطفاً فایل پی دی اف یا عکس ارسال کنید.")
    bot.register_next_step_handler(message, process_file, user_id, subject, question_text, problem)

def process_file(message: Message, user_id, subject, question_text, problem_text, attempts=0):
    if attempts >= 3:
        bot.send_message(user_id, "❌ تعداد تلاش‌های شما بیش از حد مجاز است. لطفاً مجدداً تلاش کنید.")
        send_main_menu(user_id)
        return

    if message.content_type in ["photo", "document"]:
        file_id = message.photo[-1].file_id if message.content_type == "photo" else message.document.file_id
        send_question_to_group(user_id, subject, question_text, problem_text, file_id, message.content_type)
    else:
        bot.send_message(user_id, "⚠️ لطفاً فایل پی دی اف یا عکس ارسال کنید.")
        bot.register_next_step_handler(message, lambda msg: process_file(msg, user_id, subject, question_text, problem_text, attempts+1))


def send_question_to_group(user_id, subject, question_text, problem_text, file_id=None, file_type=None):
    student = get_student(user_id)
    if student is None:
        bot.send_message(user_id, "❌ اطلاعات شما در سیستم یافت نشد. لطفاً ابتدا ثبت‌نام کنید.")
        return

    student_info = f"👤 نام: {student[1]}\n📞 شماره: {student[3]}\n🎓 پایه: {student[4]}\n📖 رشته: {student[5]}\n📝 وضعیت: پاسخ نداده❌"
    

    question_info_msg = bot.send_message(GROUP_ID, f"{student_info}\n\n📚 درس: {subject}\n❓ سوال: {question_text}\n\n{problem_text}\n\nبرای تغییر وضعیت سوال روی دکمه‌های زیر کلیک کنید:")

    forwarded_msg = None

    if file_type == "photo":
        forwarded_msg = bot.send_photo(GROUP_ID, file_id, caption=question_text)
    elif file_type == "document":
        forwarded_msg = bot.send_document(GROUP_ID, file_id, caption=question_text)
    else:
        forwarded_msg = bot.send_message(GROUP_ID, question_text)


    markup = InlineKeyboardMarkup()
    answer_button = InlineKeyboardButton("✅ پاسخ دادن به این سوال", callback_data=f"answered_{user_id}_{forwarded_msg.message_id}")
    delete_button = InlineKeyboardButton("❌ حذف سوال", callback_data=f"delete_{user_id}_{forwarded_msg.message_id}")
    markup.add(answer_button, delete_button)


    bot.edit_message_text(f"{student_info}\n\n📚 درس: {subject}\n❓ سوال: {question_text}\n\n{problem_text}\n\nبرای تغییر وضعیت سوال روی دکمه‌های زیر کلیک کنید:", GROUP_ID, question_info_msg.message_id, reply_markup=markup)
    

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO questions (user_id, subject, question) VALUES (?, ?, ?)", (user_id, subject, question_text))
    question_id = cursor.lastrowid
    conn.commit()
    conn.close()

    bot.send_message(user_id, "✅ سوال شما همراه با توضیح مشکل به پشتیبانی ارسال شد!")
    send_main_menu(user_id)

# _____________________________________________________

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def handle_delete(call):
    try:

        student_id = int(call.data.split('_')[1])
        message_id = int(call.data.split('_')[2])

        bot.delete_message(call.message.chat.id, message_id)

        bot.send_message(student_id, "❌ سوال شما از گروه حذف شد.")

        conn = sqlite3.connect("students.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM questions WHERE user_id = ? AND id = ?", (student_id, message_id))
        conn.commit()
        conn.close()

    except Exception as e:
       #  print(f"خطا در حذف سوال: {e}")
        bot.send_message(call.message.chat.id, "⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید.")




#____________________________________________________fix________________________________________________________________________


pending_answers = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith('answered_'))
def handle_answer(call):
    teacher_id = call.from_user.id
    student_id = int(call.data.split('_')[1])

    if student_id in pending_answers:
        bot.answer_callback_query(call.id, "❌ این سوال در حال حاضر در حال پاسخ‌دهی است.")
        return

    pending_answers[teacher_id] = student_id

    bot.send_message(teacher_id, "✏️ لطفاً پاسخ خود را ارسال کنید، اولین پیام شما برای دانش‌آموز فوروارد خواهد شد.")

@bot.message_handler(content_types=["text", "photo", "video", "document", "audio", "voice", "sticker"])
def forward_teacher_answer(message):
    teacher_id = message.chat.id
    student_id = pending_answers.get(teacher_id)

    if not student_id:
       #  print(f"⛔ خطا: برای دبیر {teacher_id} دانش‌آموزی پیدا نشد!")
        return  

#     print(f"📩 دریافت پیام از دبیر {teacher_id} برای دانش‌آموز {student_id}")
#     print(f"📌 نوع پیام: {message.content_type}")

    try:
        bot.send_chat_action(student_id, "typing")  # نمایش "در حال ارسال..."

        if message.content_type == "text":
            bot.send_message(student_id, message.text)
            # print("✅ پیام متنی ارسال شد.")

        elif message.content_type == "photo":
            bot.send_photo(student_id, message.photo[-1].file_id, caption=message.caption or "")
            # print("✅ عکس ارسال شد.")

        elif message.content_type == "video":
            bot.send_video(student_id, message.video.file_id, caption=message.caption or "")
            # print("✅ ویدیو ارسال شد.")

        elif message.content_type == "document":
            bot.send_document(student_id, message.document.file_id, caption=message.caption or "")
            # print("✅ فایل ارسال شد.")

        elif message.content_type == "audio":
            bot.send_audio(student_id, message.audio.file_id, caption=message.caption or "")
            # print("✅ فایل صوتی ارسال شد.")

        elif message.content_type == "voice":
            bot.send_voice(student_id, message.voice.file_id, caption=message.caption or "")
            # print("✅ ویس ارسال شد.")

        elif message.content_type == "sticker":
            bot.send_sticker(student_id, message.sticker.file_id)
            # print("✅ استیکر ارسال شد.")

       #  else:
       #      print(f"⚠️ پیام با نوع ناشناخته دریافت شد: {message.content_type}")


        conn = sqlite3.connect("students.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE questions SET status = 'پاسخ داده شده' WHERE user_id = ? AND status = 'پاسخ نداده'", (student_id,))
        conn.commit()
        conn.close()


        bot.send_message(teacher_id, "✅ پاسخ شما برای دانش‌آموز ارسال شد.")
        bot.send_message(student_id, "✅ پاسخ پشتیبان برای شما ارسال شد.")
       #  print(f"✅ پاسخ دبیر {teacher_id} برای دانش‌آموز {student_id} ارسال شد.")

        del pending_answers[teacher_id]

    except Exception as e:
       #  print(f"❌ خطا در ارسال پیام برای {student_id}: {e}")
        bot.send_message(teacher_id, f"⚠️ خطا در ارسال پیام: {e}")



bot.polling()
       