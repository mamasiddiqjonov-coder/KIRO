"""
Navbat Bot — asosiy ishga tushiruvchi fayl.

Ishlatish:
    1. config.example.py -> config.py qiling va to'ldiring
    2. pip install -r requirements.txt
    3. python main.py

Bu fayl hamma qismlarni (database, booking, handlers, admin) birlashtiradi
va Telegram'ga ulaydi.
"""

import logging
import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

import config
from bot.database import Database
from bot.booking import BookingManager
from bot.handlers import ClientHandlers
from bot.admin import AdminHandlers, ADD_NAME, ADD_PRICE, ADD_DURATION


# Log sozlamasi — terminalda nima bo'layotganini ko'rsatadi
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_notify_admins(admin_ids: list[int]):
    """
    Adminlarga xabar yuboruvchi funksiya yaratadi.
    handlers.py uni context.bot_data orqali ishlatadi (yangi bron bo'lganda).
    """
    async def notify_admins(context: ContextTypes.DEFAULT_TYPE, text: str):
        for admin_id in admin_ids:
            try:
                await context.bot.send_message(chat_id=admin_id, text=text)
            except Exception as e:
                logger.warning("Adminga (%s) xabar yuborilmadi: %s", admin_id, e)

    return notify_admins


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Kutilmagan xatolarni loglaydi (bot to'xtab qolmasligi uchun)."""
    logger.error("Xatolik yuz berdi:", exc_info=context.error)


def main():
    # Python 3.12+ / 3.14 da event loop avtomatik yaratilmaydi.
    # Shuning uchun o'zimiz yaratib, joriy thread'ga ulaymiz.
    # Bu "There is no current event loop" xatosini oldini oladi.
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    # --- Qismlarni quramiz ---
    db = Database(config.DB_PATH)
    booking = BookingManager(
        db,
        work_start_hour=config.WORK_START_HOUR,
        work_end_hour=config.WORK_END_HOUR,
        slot_minutes=config.DEFAULT_SLOT_MINUTES,
        days_ahead=config.BOOKING_DAYS_AHEAD,
    )
    client = ClientHandlers(db, booking, config.BUSINESS_NAME)
    admin = AdminHandlers(db, config.ADMIN_IDS, config.BUSINESS_NAME)

    # --- Application (bot) ---
    app = Application.builder().token(config.BOT_TOKEN).build()

    # Adminlarga xabar yuborish funksiyasini handlerlar uchun saqlaymiz
    app.bot_data["notify_admins"] = build_notify_admins(config.ADMIN_IDS)

    # ============ MIJOZ buyruqlari ============
    app.add_handler(CommandHandler("start", client.start))

    # Asosiy menyu tugmalari (matn orqali)
    app.add_handler(MessageHandler(
        filters.Regex("^📅 Navbat olish$"), client.choose_service))
    app.add_handler(MessageHandler(
        filters.Regex("^📋 Mening navbatlarim$"), client.my_bookings))
    app.add_handler(MessageHandler(
        filters.Regex("^ℹ️ Ma'lumot$"), client.info))

    # Bron jarayoni (inline tugmalar)
    app.add_handler(CallbackQueryHandler(client.on_service_selected, pattern=r"^svc:"))
    app.add_handler(CallbackQueryHandler(client.on_day_selected, pattern=r"^day:"))
    app.add_handler(CallbackQueryHandler(client.on_time_selected, pattern=r"^time:"))
    app.add_handler(CallbackQueryHandler(client.on_confirm, pattern=r"^confirm$"))
    app.add_handler(CallbackQueryHandler(client.on_cancel_booking, pattern=r"^cancel:"))
    app.add_handler(CallbackQueryHandler(client.on_back_to_services, pattern=r"^back:services$"))

    # ============ ADMIN buyruqlari ============
    app.add_handler(CommandHandler("admin", admin.admin_menu))
    app.add_handler(MessageHandler(
        filters.Regex("^📅 Bugungi navbatlar$"), admin.today_bookings))
    app.add_handler(MessageHandler(
        filters.Regex("^📆 Ertangi navbatlar$"), admin.tomorrow_bookings))
    app.add_handler(MessageHandler(
        filters.Regex("^🛠 Xizmatlar$"), admin.list_services))
    app.add_handler(MessageHandler(
        filters.Regex("^📊 Statistika$"), admin.stats))
    app.add_handler(CallbackQueryHandler(admin.on_delete_service, pattern=r"^delsvc:"))

    # Xizmat qo'shish — suhbat (ConversationHandler)
    add_service_conv = ConversationHandler(
        entry_points=[MessageHandler(
            filters.Regex("^➕ Xizmat qo'shish$"), admin.add_start)],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_name)],
            ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_price)],
            ADD_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_duration)],
        },
        fallbacks=[CommandHandler("bekor", admin.add_cancel)],
    )
    app.add_handler(add_service_conv)

    # Xatolarni ushlash
    app.add_error_handler(on_error)

    # --- Ishga tushiramiz ---
    logger.info("Bot ishga tushdi. To'xtatish uchun Ctrl+C bosing.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
