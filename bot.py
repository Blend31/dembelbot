# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime, timedelta
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from datetime import datetime, time, timedelta # datetime уже импортирован
from zoneinfo import ZoneInfo
from telegram.ext import PicklePersistence

# --- НОВЫЙ КОД ДЛЯ HEALTH CHECK ---
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
# --- КОНЕЦ НОВОГО КОДА ---

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- НОВЫЙ КОД: HTTP Handler и функция запуска сервера ---
RENDER_PORT = int(os.environ.get('PORT', 10000)) # Render выставляет PORT

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is alive!")
        # logger.info("Health check request received and responded.") # Можно раскомментировать для отладки
     def do_HEAD(self): # <--- ДОБАВЬТЕ ЭТО
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
         
def run_health_check_server():
    server_address = ('', RENDER_PORT) # Слушаем на всех интерфейсах на порту от Render
    try:
        httpd = HTTPServer(server_address, HealthCheckHandler)
        logger.info(f"Health check HTTP server_legacy_subtitles_settings_dialog_ok_button running on port {RENDER_PORT}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Could not start or run health check server_legacy_subtitles_settings_dialog_ok_button: {e}", exc_info=True)
# --- КОНЕЦ НОВОГО КОДА ---

# ... (остальной ваш код без изменений: DATE_INPUT, MOTIVATION_PHRASES, и т.д.)
# Состояния разговора
DATE_INPUT, MAIN_MENU = range(2)

# Мотивационные фразы для разного оставшегося времени
MOTIVATION_PHRASES = {
    "long": [
        "ВПЕРЕДИ ЕЩЕ МНОГО УЧЕБНЫХ ЧАСОВ, КУРСАНТ! КРЕПИТЕСЬ!",
        "ПУТЬ К ОФИЦЕРСКИМ ПОГОНАМ ДОЛОГ, НО ПОЧЕТЕН!",
        "УЧЕБА ПРОДОЛЖАЕТСЯ! НЕ СБАВЛЯЙТЕ ТЕМП, БУДУЩИЙ ОФИЦЕР!",
        "КАЖДЫЙ ДЕНЬ ПРИБЛИЖАЕТ ВАС К ОФИЦЕРСКОМУ ЗВАНИЮ!",
        "УСЕРДИЕ В УЧЕБЕ СЕГОДНЯ — УСПЕХ В СЛУЖБЕ ЗАВТРА!"
    ],
    "medium": [
        "ЭКВАТОР ПОЗАДИ! СТАНОВИТЕСЬ БЛИЖЕ К ОФИЦЕРСКОМУ ЗВАНИЮ!",
        "УЖЕ БОЛЬШЕ ПОЛОВИНЫ УЧЕБЫ ЗАВЕРШЕНО! ТАК ДЕРЖАТЬ!",
        "ВИДНА ФИНИШНАЯ ПРЯМАЯ, КУРСАНТ! ВПЕРЕДИ ОФИЦЕРСКИЕ ПОГОНЫ!",
        "ПРОДОЛЖАЙТЕ В ТОМ ЖЕ ДУХЕ! РОДИНА ЖДЕТ ВАШИХ ЗНАНИЙ!",
        "НАСТОЙЧИВОСТЬ И ТРУД ВАС К ВЫПУСКУ ПРИВЕДУТ!"
    ],
    "short": [
        "ГОСУДАРСТВЕННЫЕ ЭКЗАМЕНЫ НА ГОРИЗОНТЕ! ДЕРЖИТЕСЬ, КУРСАНТ!",
        "СКОРО ПОЛУЧИТЕ ПЕРВОЕ ОФИЦЕРСКОЕ ЗВАНИЕ! ВЫДЕРЖИТЕ ФИНАЛЬНЫЙ РЫВОК!",
        "СОВСЕМ НЕМНОГО ОСТАЛОСЬ ДО ВЫПУСКА! ЧЕСТЬ ИМЕЮ!",
        "ВПЕРЕДИ ВРУЧЕНИЕ ПОГОН! БУДЬТЕ ДОСТОЙНЫ ВЫСОКОГО ЗВАНИЯ!",
        "ПОСЛЕДНИЕ РУБЕЖИ ПЕРЕД ОФИЦЕРСКИМ ЗВАНИЕМ! НЕ СДАВАЙТЕСЬ!"
    ],
    "almost": [
        "ГОТОВЬТЕ ПАРАДНУЮ ФОРМУ! ВЫПУСК СОВСЕМ СКОРО!",
        "СЧИТАННЫЕ ДНИ ДО ПРИСВОЕНИЯ ЗВАНИЯ! ДЕРЖИТЕСЬ, КУРСАНТ!",
        "СОВСЕМ СКОРО ВЫ СТАНЕТЕ ОФИЦЕРОМ! РОДИНА ГОРДИТСЯ ТОБОЙ!",
        "ОФИЦЕРСКИЕ ПОГОНЫ УЖЕ ЖДУТ ВАС! ФИНАЛЬНЫЙ РЫВОК!",
        "ВЫ НА ПОРОГЕ НОВОЙ ЖИЗНИ! ЧЕСТЬ И СЛАВА ВЫПУСКНИКАМ!"
    ]
}

# Цитаты великих военачальников
MILITARY_QUOTES = [
    "«Плох тот солдат, который не мечтает стать генералом» — А.В. Суворов",
    "«Тяжело в учении, легко в бою» — А.В. Суворов",
    "«Дисциплина — мать победы» — А.В. Суворов",
    "«Кто напуган — наполовину побит» — А.В. Суворов",
    "«Войско необученное — что сабля неотточенная» — М.И. Кутузов",
    "«Где мужество, там победа» — Г.К. Жуков",
    "«Кто хочет много знать, тому надо мало спать» — А.В. Суворов",
    "«Наука побеждать должна быть творческой» — М.В. Фрунзе",
    "«Полководец истинный ведет войско, а не войско его» — М.И. Драгомиров",
    "«Офицер — это не звание, а призвание» — народная мудрость"
]

# ASCII арт для бота
ACADEMY_ASCII = """
★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★
╔══════════════════════════╗
║   СЧЕТЧИК ДО ВЫПУСКА    
╚══════════════════════════╝
   🎖️  🪖  🎖️  🪖  🎖️  🪖
"""

# Разделитель для сообщений
DIVIDER = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"


def create_progress_bar(days_left, total_days=1825):  # Примерно 5 лет обучения (1825 дней)
    """Создает визуальный прогресс-бар обучения"""
    if days_left < 0:
        return "[ВЫПУСК!]"

    # Оценка прогресса
    days_passed = total_days - days_left
    if days_passed > total_days:  # Для случая, если осталось меньше 0 дней
        days_passed = total_days
    if days_passed < 0: # Если дата выпуска в далеком будущем, days_passed может быть < 0
        days_passed = 0


    percentage = int((days_passed / total_days) * 10) if total_days > 0 else 0


    progress = "▓" * percentage + "░" * (10 - percentage)
    percent_num = int((days_passed / total_days) * 100) if total_days > 0 else 0


    return f"[{progress}] {percent_num}%"


def get_motivation(days_left, total_days=1825):
    """Возвращает мотивационную фразу в зависимости от оставшегося времени"""
    if days_left <= 0:
        return "ПОЗДРАВЛЯЮ, ЛЕЙТЕНАНТ! ЧЕСТЬ ИМЕЮ!"

    percent_left = (days_left / total_days) * 100 if total_days > 0 else 100


    if percent_left > 70:
        return random.choice(MOTIVATION_PHRASES["long"])
    elif percent_left > 30:
        return random.choice(MOTIVATION_PHRASES["medium"])
    elif percent_left > 10:
        return random.choice(MOTIVATION_PHRASES["short"])
    else:
        return random.choice(MOTIVATION_PHRASES["almost"])


def get_next_milestone(target_date, today):
    """Определяет ближайшую важную веху перед выпуском"""
    days_left = (target_date - today).days

    # Примерные важные вехи перед выпуском
    milestones = []

    # Если до выпуска больше 100 дней, добавляем стодневку
    if days_left > 100:
        hundred_days = target_date - timedelta(days=100)
        milestones.append(("100 ДНЕЙ ДО ВЫПУСКА", (hundred_days - today).days, 2))

    # Если до выпуска больше 60 дней, добавляем госэкзамены
    if days_left > 60:
        state_exams = target_date - timedelta(days=60)
        milestones.append(("ГОСЭКЗАМЕНЫ", (state_exams - today).days, 3))

    # Если до выпуска больше 30 дней, добавляем защиту диплома
    if days_left > 30:
        thesis_defense = target_date - timedelta(days=30)
        milestones.append(("ЗАЩИТА ДИПЛОМА", (thesis_defense - today).days, 3))

    # Если до выпуска больше 10 дней, добавляем последние приготовления
    if days_left > 10:
        final_prep = target_date - timedelta(days=10)
        milestones.append(("ПОСЛЕДНИЕ ПРИГОТОВЛЕНИЯ", (final_prep - today).days, 2))

    # Если до выпуска больше 1 дня, добавляем репетицию выпуска
    if days_left > 1:
        rehearsal = target_date - timedelta(days=1)
        milestones.append(("РЕПЕТИЦИЯ ВЫПУСКА", (rehearsal - today).days, 2))

    # Фильтруем и сортируем вехи, оставляя только те, которые в будущем
    future_milestones = [(name, days, importance) for name, days, importance in milestones
                         if days > 0]
    future_milestones.sort(key=lambda x: x[1])  # Сортируем по времени до события

    return future_milestones[0] if future_milestones else None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало разговора и запрос даты."""
    logger.info(f"Получена команда /start от пользователя {update.effective_user.id}")

    # Отправляем ASCII-арт с инструкциями в одном сообщении
    await update.message.reply_text(
        f"{ACADEMY_ASCII}\n"
        "ПРИВЕТСТВУЮ, КУРСАНТ! 🎖️\n\n"
        "УЧЕБНАЯ ЧАСТЬ ЗАПРАШИВАЕТ ДАННЫЕ!\n\n"
        "УКАЖИТЕ ДАТУ ВЫПУСКА:\n\n"
        "ФОРМАТ: ДД.ММ.ГГГГ\n"
        "НАПРИМЕР: 25.06.2026"
    )

    return DATE_INPUT


async def calculate_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка введенной даты и расчет оставшихся дней."""
    logger.info(f"Получено сообщение с датой от пользователя {update.effective_user.id}: {update.message.text}")

    user_text = update.message.text

    try:
        # Парсим дату выпуска
        target_date_dt = datetime.strptime(user_text, "%d.%m.%Y") # Изменено имя переменной для ясности
        # Для расчетов и хранения лучше использовать только дату, без времени, если оно не важно
        target_date = target_date_dt.date()
        today = datetime.now().date()


        # Расчеты
        days_left = (target_date - today).days


        # Сохраняем дату в контексте
        # context.user_data['target_date'] = target_date # Сохраняем объект date
        context.user_data['target_date_iso'] = target_date.isoformat() # Храним как строку ISO для PicklePersistence

        tz_str = context.user_data.get("tz", "Europe/Moscow") # Пример, лучше брать из настроек пользователя или запрашивать


        # Ставим/переставляем ежедневный job
        reschedule_daily_job(context, update.effective_chat.id, target_date, tz_str)


        # Прогресс-бар (оценочный, без даты начала)
        progress_bar = create_progress_bar(days_left)

        # Мотивационная фраза
        motivation = get_motivation(days_left)

        # Получаем информацию о ближайшей важной вехе
        next_milestone = get_next_milestone(target_date, today)

        # Добавляем случайную цитату
        quote = random.choice(MILITARY_QUOTES)

        # Формируем ответ
        if days_left < 0:
            response = (
                f"⭐️ ДОКЛАДЫВАЮ! ⭐️\n\n"
                f"ВЫ УЖЕ {abs(days_left)} ДНЕЙ КАК ОФИЦЕР!\n"
                f"ПОЗДРАВЛЯЮ С УСПЕШНЫМ ОКОНЧАНИЕМ ВОЕННОГО УНИВЕРСИТЕТА, ТОВАРИЩ ЛЕЙТЕНАНТ!"
            )
        elif days_left == 0:
            response = (
                f"⭐️⭐️⭐️ ВНИМАНИЕ! СЕГОДНЯ ВЫПУСК! ⭐️⭐️⭐️\n\n"
                f"ПОЗДРАВЛЯЮ! ПРИКАЗ О ПРИСВОЕНИИ ЗВАНИЯ ПОДПИСАН!\n"
                f"ЧЕСТЬ ИМЕЮ, ТОВАРИЩ ЛЕЙТЕНАНТ!"
            )
        else:
            # Информация о вехе
            if next_milestone:
                milestone_name, days_to_milestone, importance = next_milestone
                milestone_markers = "‼️" if importance == 3 else "❗️"
                milestone_info = f"\n{milestone_markers} БЛИЖАЙШЕЕ СОБЫТИЕ: {milestone_name} ЧЕРЕЗ {days_to_milestone} ДНЕЙ"
            else:
                milestone_info = ""

            # Оценка текущего курса на основе дней до выпуска (для 5 лет обучения)
            estimated_course = 5  # По умолчанию последний курс
            if days_left > 365 * 4:  # Больше 4 лет
                estimated_course = 1
            elif days_left > 365 * 3:  # Больше 3 лет
                estimated_course = 2
            elif days_left > 365 * 2:  # Больше 2 лет
                estimated_course = 3
            elif days_left > 365:  # Больше 1 года
                estimated_course = 4

            response = (
                f"⭐️ СВОДКА НА СЕГОДНЯ, КУРСАНТ! ⭐️\n\n"
                f"ДО ВЫПУСКА: {days_left} ДНЕЙ\n"
                f"{DIVIDER}\n"
                f"ПРОГРЕСС ОБУЧЕНИЯ: {progress_bar}\n"
                f"ПРЕДПОЛАГАЕМЫЙ КУРС: {estimated_course}\n"
                f"{milestone_info}\n"
                f"{DIVIDER}\n"
                f"➤ {motivation}\n\n"
                f"💭 {quote}"
            )

            # Добавляем фразы для особых случаев
            if days_left == 100:
                response += "\n\n💯 РОВНО 100 ДНЕЙ ДО ВЫПУСКА! ДЕРЖИТЕСЬ!"
            elif days_left <= 30 and days_left > 0 : # Добавил >0, чтобы не показывать для выпускников
                response += f"\n\n🎖️ МЕНЬШЕ МЕСЯЦА ДО ПРИСВОЕНИЯ ЗВАНИЯ!"
            elif 60 <= days_left <= 70:
                response += f"\n\n📚 ГОСЭКЗАМЕНЫ ПРИБЛИЖАЮТСЯ! БУДЬТЕ ГОТОВЫ!"

        # Добавляем кнопки (без учебного плана и традиций)
        keyboard = [
            ['📊 ОБНОВИТЬ ДАННЫЕ'],
            ['🔄 ИЗМЕНИТЬ ДАТУ']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        # Отправляем сообщение с результатом и кнопками
        await update.message.reply_text(response, reply_markup=reply_markup)

        logger.info(f"Отправлен ответ с расчетом дней пользователю {update.effective_user.id}")
        return MAIN_MENU

    except ValueError as e:
        logger.error(f"Ошибка формата даты от пользователя {update.effective_user.id}: {e}", exc_info=True)
        await update.message.reply_text(
            "⚠️ ОШИБКА В ФОРМАТЕ ДАТЫ! ⚠️\n\n"
            "УКАЖИТЕ ДАТУ ВЫПУСКА В ФОРМАТЕ ДД.ММ.ГГГГ\n"
            "НАПРИМЕР: 25.06.2026"
        )
        return DATE_INPUT


async def check_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обновляет информацию о днях до выпуска."""
    logger.info(f"Получена команда обновления данных от пользователя {update.effective_user.id}")

    # if 'target_date' not in context.user_data: # Проверяем по ISO строке
    if 'target_date_iso' not in context.user_data:
        await update.message.reply_text(
            "⚠️ НЕТ ДАННЫХ О ВЫПУСКЕ! ⚠️\n"
            "ИСПОЛЬЗУЙТЕ /start ДЛЯ ВВОДА ДАТЫ."
        )
        # Если ConversationHandler активен, но нет данных, лучше вернуть его в начало или текущее состояние,
        # а не ConversationHandler.END, если это нежелательно.
        # Но если мы в MAIN_MENU и данных нет, то можно и END.
        # Для простоты, если вызвали check_days, а данных нет, это ошибка, можно и завершить.
        return ConversationHandler.END # Или DATE_INPUT, если хотите сразу запросить дату

    # target_date = context.user_data['target_date'] # Берем ISO строку и конвертируем
    target_date = datetime.fromisoformat(context.user_data['target_date_iso']).date()
    today = datetime.now().date()


    # Расчеты
    days_left = (target_date - today).days

    # Прогресс-бар
    progress_bar = create_progress_bar(days_left)

    # Мотивационная фраза
    motivation = get_motivation(days_left)

    # Получаем информацию о ближайшей важной вехе
    next_milestone = get_next_milestone(target_date, today)

    # Добавляем случайную цитату
    quote = random.choice(MILITARY_QUOTES)

    # Формируем ответ (аналогично calculate_days)
    if days_left < 0:
        response = (
            f"⭐️ ДОКЛАДЫВАЮ! ⭐️\n\n"
            f"ВЫ УЖЕ {abs(days_left)} ДНЕЙ КАК ОФИЦЕР!\n"
            f"ПОЗДРАВЛЯЮ С УСПЕШНЫМ ОКОНЧАНИЕМ ВОЕННОГО УНИВЕРСИТЕТА, ТОВАРИЩ ЛЕЙТЕНАНТ!"
        )
    elif days_left == 0:
        response = (
            f"⭐️⭐️⭐️ ВНИМАНИЕ! СЕГОДНЯ ВЫПУСК! ⭐️⭐️⭐️\n\n"
            f"ПОЗДРАВЛЯЮ! ПРИКАЗ О ПРИСВОЕНИИ ЗВАНИЯ ПОДПИСАН!\n"
            f"ЧЕСТЬ ИМЕЮ, ТОВАРИЩ ЛЕЙТЕНАНТ!"
        )
    else:
        # Информация о вехе
        if next_milestone:
            milestone_name, days_to_milestone, importance = next_milestone
            milestone_markers = "‼️" if importance == 3 else "❗️"
            milestone_info = f"\n{milestone_markers} БЛИЖАЙШЕЕ СОБЫТИЕ: {milestone_name} ЧЕРЕЗ {days_to_milestone} ДНЕЙ"
        else:
            milestone_info = ""

        # Оценка текущего курса на основе дней до выпуска (для 5 лет обучения)
        estimated_course = 5  # По умолчанию последний курс
        if days_left > 365 * 4:  # Больше 4 лет
            estimated_course = 1
        elif days_left > 365 * 3:  # Больше 3 лет
            estimated_course = 2
        elif days_left > 365 * 2:  # Больше 2 лет
            estimated_course = 3
        elif days_left > 365:  # Больше 1 года
            estimated_course = 4

        response = (
            f"⭐️ ОБНОВЛЕННЫЕ ДАННЫЕ, КУРСАНТ! ⭐️\n\n"
            f"ДО ВЫПУСКА: {days_left} ДНЕЙ\n"
            f"{DIVIDER}\n"
            f"ПРОГРЕСС ОБУЧЕНИЯ: {progress_bar}\n"
            f"ПРЕДПОЛАГАЕМЫЙ КУРС: {estimated_course}\n"
            f"{milestone_info}\n"
            f"{DIVIDER}\n"
            f"➤ {motivation}\n\n"
            f"💭 {quote}"
        )

        # Добавляем фразы для особых случаев
        if days_left == 100:
            response += "\n\n💯 РОВНО 100 ДНЕЙ ДО ВЫПУСКА! ДЕРЖИТЕСЬ!"
        elif days_left <= 30 and days_left > 0:
            response += f"\n\n🎖️ МЕНЬШЕ МЕСЯЦА ДО ПРИСВОЕНИЯ ЗВАНИЯ!"
        elif 60 <= days_left <= 70:
            response += f"\n\n📚 ГОСЭКЗАМЕНЫ ПРИБЛИЖАЮТСЯ! БУДЬТЕ ГОТОВЫ!"

    # Добавляем кнопки (без учебного плана и традиций)
    keyboard = [
        ['📊 ОБНОВИТЬ ДАННЫЕ'],
        ['🔄 ИЗМЕНИТЬ ДАТУ']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(response, reply_markup=reply_markup)
    logger.info(f"Отправлены обновленные данные пользователю {update.effective_user.id}")
    return MAIN_MENU


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сбрасывает данные и сразу начинает процесс заново."""
    logger.info(f"Получена команда сброса данных от пользователя {update.effective_user.id}")

    # Очищаем данные пользователя
    context.user_data.clear()

    # Удаляем старый job, если он был
    for old_job in context.job_queue.get_jobs_by_name(str(update.effective_chat.id)):
        old_job.schedule_removal()
        logger.info(f"Удален старый job для чата {update.effective_chat.id} при сбросе.")


    # Отправляем сообщение о сбросе и сразу запрашиваем новую дату
    await update.message.reply_text(
        f"{ACADEMY_ASCII}\n"
        "ДАННЫЕ СБРОШЕНЫ! НАЧИНАЕМ ЗАНОВО!\n\n"
        "ПРИВЕТСТВУЮ, КУРСАНТ! 🎖️\n\n"
        "УКАЖИТЕ ДАТУ ВЫПУСКА:\n\n"
        "ФОРМАТ: ДД.ММ.ГГГГ\n"
        "НАПРИМЕР: 25.06.2026"
    )

    # Переходим к состоянию ввода даты
    return DATE_INPUT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена разговора."""
    logger.info(f"Получена команда отмены от пользователя {update.effective_user.id}")
    await update.message.reply_text("ОПЕРАЦИЯ ОТМЕНЕНА, КУРСАНТ!")
    return ConversationHandler.END

async def morning_message(context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет утреннее сообщение «Доброе утро! До выпуска …»
    Вызывается job'ом JobQueue.
    """
    job_data = context.job.data          # то, что мы передали при создании job
    chat_id   = job_data["chat_id"]
    target_iso= job_data["target_date_iso"]  # 'YYYY-MM-DD'
    tz_str    = job_data["tz"]           # 'Europe/Moscow' и т.п.

    try:
        target_date_obj = datetime.fromisoformat(target_iso).date() # Используем .date() для сравнения только дат
        today       = datetime.now(ZoneInfo(tz_str)).date()
        days_left   = (target_date_obj - today).days

        if days_left < 0:
            text = f"🎉 Доброе утро! Вы уже {abs(days_left)} дн. как офицер!"
        elif days_left == 0:
            text = "🏁 Доброе утро! Сегодня выпуск! Поздравляем! 🎓"
        else:
            text = f"🌞 Доброе утро! До выпуска осталось {days_left} дн."

        await context.bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"Утреннее сообщение отправлено в чат {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка в morning_message для чата {chat_id}: {e}", exc_info=True)

def reschedule_daily_job(context: ContextTypes.DEFAULT_TYPE,
                         chat_id: int,
                         target_date_obj: datetime.date, # Принимаем объект date
                         tz_str: str = "Europe/Moscow",  # Установите ваш часовой пояс по умолчанию
                         hour: int = 7, minute: int = 0): # Изменено на 7 утра, как пример
    """
    Снимает старый job (если был) и ставит новый, который будет
    каждый день в <hour:minute> по tz_str слать morning_message.
    """
    job_name = str(chat_id)
    # 1) удаляем существующие
    for old_job in context.job_queue.get_jobs_by_name(job_name):
        old_job.schedule_removal()
        logger.info(f"Удален предыдущий job '{job_name}'")


    # 2) ставим новый
    # Убедимся, что target_date_obj это date, а не datetime
    if isinstance(target_date_obj, datetime):
        target_date_to_store = target_date_obj.date()
    else:
        target_date_to_store = target_date_obj

    context.job_queue.run_daily(
        morning_message,
        time=time(hour=hour, minute=minute, tzinfo=ZoneInfo(tz_str)),
        name=job_name,                       # чтобы легко найти/удалить
        data={
            "chat_id": chat_id,
            "target_date_iso": target_date_to_store.isoformat(), # Храним ISO строку
            "tz": tz_str
        }
    )
    logger.info(f"Ежедневный job '{job_name}' запланирован на {hour:02d}:{minute:02d} ({tz_str}) для даты {target_date_to_store.isoformat()}")


def main():
    # Определяем путь к файлу персистентности ОДИН РАЗ ВНАЧАЛЕ
    # Используем абсолютный путь для надежности на сервере
    persistence_file_path = "/opt/render/project/src/bot_data_persistence.pkl"
    # или, если хотите протестировать /tmp/:
    # persistence_file_path = "/tmp/bot_data_persistence.pkl"

    # --- ВРЕМЕННЫЙ КОД ДЛЯ ПРОВЕРКИ/СОЗДАНИЯ PERSISTENCE ---
    # (Используйте тот обновленный код, который я дал в предыдущем ответе,
    #  который пытается создать валидный пустой pickle-файл, если файла нет или он нулевой)
    import os
    import pickle
    # Вставьте сюда обновленный временный код, работающий с persistence_file_path
    # Пример (сокращенный, используйте полную версию из прошлого ответа):
    if not os.path.exists(persistence_file_path) or (os.path.exists(persistence_file_path) and os.path.getsize(persistence_file_path) == 0):
        if os.path.exists(persistence_file_path): # если был нулевой, удаляем
            os.remove(persistence_file_path)
        logger.info(f"Файл {persistence_file_path} не найден или был нулевым. Создание нового валидного пустого файла.")
        try:
            empty_data = {"user_data": {}, "chat_data": {}, "bot_data": {}, "conversations": {}, "callback_persistence": None}
            with open(persistence_file_path, "wb") as f:
                pickle.dump(empty_data, f)
            logger.info(f"Создан новый пустой, но валидный файл персистентности: {persistence_file_path}")
        except Exception as e_create:
            logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать файл персистентности {persistence_file_path}: {e_create}")
            return # Выход, если не можем создать файл
    else:
        logger.info(f"Файл персистентности {persistence_file_path} найден и не нулевой.")
    # --- КОНЕЦ ВРЕМЕННОГО КОДА ---

    try:
        BOT_TOKEN = os.getenv("BOT_TOKEN")
        if not BOT_TOKEN:
            logger.critical("Переменная окружения BOT_TOKEN не найдена!")
            raise RuntimeError("Переменная окружения BOT_TOKEN не найдена!")

        health_thread = threading.Thread(target=run_health_check_server, daemon=True)
        health_thread.start()

        # Создаем объект PicklePersistence ОДИН РАЗ, используя определенный ранее путь
        my_persistence = PicklePersistence(
            filepath=persistence_file_path
            # Если хотите протестировать отключение сохранения JobQueue:
            # store_callback_data=False
        )
        logger.info(f"PicklePersistence инициализирован с файлом: {persistence_file_path}")


        application = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .persistence(my_persistence)
            .build()
        )

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                DATE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, calculate_days)],
                MAIN_MENU: [
                    MessageHandler(filters.Regex('^📊 ОБНОВИТЬ ДАННЫЕ$') | filters.Command("check"), check_days),
                    MessageHandler(filters.Regex('^🔄 ИЗМЕНИТЬ ДАТУ$'), reset),
                    CommandHandler("reset", reset),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            name="graduation_counter_conversation",
            persistent=True
        )

        application.add_handler(conv_handler)

        async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Извините, я не понимаю эту команду. Используйте /start")
        application.add_handler(MessageHandler(filters.COMMAND, unknown))

        logger.info("Бот запускается...")
        application.run_polling()

    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске или работе бота: {e}", exc_info=True)

if __name__ == "__main__":
    main()
