"""
Mijoz tomoni — Telegram interfeysi.

Bron jarayoni (inline tugmalar orqali):
  /start  ->  asosiy menyu
  "Navbat olish"  ->  xizmat tanlash  ->  kun tanlash  ->  vaqt tanlash  ->  tasdiqlash
  "Mening navbatlarim"  ->  ro'yxat + bekor qilish

Holat (qaysi xizmat/kun tanlangani) context.user_data da saqlanadi.
callback_data formati: "harakat:qiymat"  (masalan "svc:3", "day:2026-06-02", "time:...").
"""

from datetime import date, datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import ContextTypes

from .booking import BookingManager
from .database import Database
from . import utils


# Asosiy menyu tugmalari (pastdagi doimiy klaviatura)
MAIN_KB = ReplyKeyboardMarkup(
    [
        ["📅 Navbat olish"],
        ["📋 Mening navbatlarim"],
        ["ℹ️ Ma'lumot"],
    ],
    resize_keyboard=True,
)


class ClientHandlers:
    """
    Mijoz buyruqlarini boshqaruvchi klass.
    db, booking manager va biznes nomini saqlaydi.
    """

    def __init__(self, db: Database, booking: BookingManager, business_name: str):
        self.db = db
        self.booking = booking
        self.business_name = business_name

    # ===============================================================
    # /start va asosiy menyu
    # ===============================================================

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        # Mijozni bazaga yozib qo'yamiz (ismi bilan)
        self.db.get_or_create_client(user.id, name=user.full_name)

        text = (
            f"Assalomu alaykum, {user.first_name}! 👋\n\n"
            f"*{self.business_name}* navbat olish botiga xush kelibsiz.\n\n"
            "Quyidagi tugmalardan birini tanlang:"
        )
        await update.message.reply_text(
            text, reply_markup=MAIN_KB, parse_mode="Markdown"
        )

    async def info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        ws = self.booking.work_start_hour
        we = self.booking.work_end_hour
        text = (
            f"*{self.business_name}*\n\n"
            f"🕒 Ish vaqti: {ws:02d}:00 – {we:02d}:00\n"
            f"📅 {self.booking.days_ahead} kun oldindan navbat olish mumkin\n\n"
            "Navbat olish uchun «📅 Navbat olish» tugmasini bosing."
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    # ===============================================================
    # 1-qadam: Xizmat tanlash
    # ===============================================================

    async def choose_service(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        services = self.db.get_services(only_active=True)
        if not services:
            await update.message.reply_text(
                "Hozircha xizmatlar qo'shilmagan. Iltimos keyinroq urinib ko'ring."
            )
            return

        buttons = [
            [InlineKeyboardButton(
                utils.service_label(s["name"], s["price"], s["duration"]),
                callback_data=f"svc:{s['id']}",
            )]
            for s in services
        ]
        await update.message.reply_text(
            "Qaysi xizmatga yozilmoqchisiz?",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    # ===============================================================
    # 2-qadam: Kun tanlash
    # ===============================================================

    async def on_service_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        service_id = int(query.data.split(":")[1])

        service = self.db.get_service(service_id)
        if service is None:
            await query.edit_message_text("Bu xizmat endi mavjud emas.")
            return

        # Tanlovni eslab qolamiz
        context.user_data["service_id"] = service_id

        buttons = []
        for d in self.booking.available_days():
            buttons.append([InlineKeyboardButton(
                utils.format_day(d),
                callback_data=f"day:{d.isoformat()}",
            )])
        buttons.append([InlineKeyboardButton("« Orqaga", callback_data="back:services")])

        await query.edit_message_text(
            f"*{service['name']}* — qaysi kun?",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown",
        )

    # ===============================================================
    # 3-qadam: Vaqt tanlash
    # ===============================================================

    async def on_day_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        day = date.fromisoformat(query.data.split(":", 1)[1])

        service_id = context.user_data.get("service_id")
        service = self.db.get_service(service_id) if service_id else None
        if service is None:
            await query.edit_message_text(
                "Nimadir xato ketdi. /start bosib qaytadan boshlang."
            )
            return

        context.user_data["day"] = day.isoformat()

        free = self.booking.get_free_slots(day, duration=service["duration"])
        if not free:
            await query.edit_message_text(
                f"{utils.format_day(day)} uchun bo'sh vaqt qolmadi. 😔\n"
                "Boshqa kun tanlang.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("« Kunlar", callback_data=f"svc:{service_id}")]]
                ),
            )
            return

        # Vaqtlarni qatorga 3 tadan joylashtiramiz
        buttons = []
        row = []
        for slot in free:
            row.append(InlineKeyboardButton(
                utils.format_time(slot),
                callback_data=f"time:{slot.isoformat()}",
            ))
            if len(row) == 3:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton("« Kunlar", callback_data=f"svc:{service_id}")])

        await query.edit_message_text(
            f"*{service['name']}*\n{utils.format_day(day)}\n\nBo'sh vaqtni tanlang:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown",
        )

    # ===============================================================
    # 4-qadam: Tasdiqlash
    # ===============================================================

    async def on_time_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        start = datetime.fromisoformat(query.data.split(":", 1)[1])

        service_id = context.user_data.get("service_id")
        service = self.db.get_service(service_id) if service_id else None
        if service is None:
            await query.edit_message_text(
                "Nimadir xato ketdi. /start bosib qaytadan boshlang."
            )
            return

        context.user_data["start"] = start.isoformat()

        price = utils.format_price(service["price"])
        price_line = f"\n💰 Narxi: {price}" if price else ""
        text = (
            "Navbatni tasdiqlang:\n\n"
            f"🔹 Xizmat: *{service['name']}*\n"
            f"🕒 Vaqt: *{utils.format_datetime(start)}*"
            f"{price_line}"
        )
        buttons = [
            [InlineKeyboardButton("✅ Tasdiqlayman", callback_data="confirm")],
            [InlineKeyboardButton("« Vaqtlar", callback_data=f"day:{start.date().isoformat()}")],
        ]
        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown"
        )

    async def on_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        service_id = context.user_data.get("service_id")
        start_iso = context.user_data.get("start")
        if not service_id or not start_iso:
            await query.edit_message_text(
                "Nimadir xato ketdi. /start bosib qaytadan boshlang."
            )
            return

        start = datetime.fromisoformat(start_iso)
        user = update.effective_user

        result = self.booking.book(
            tg_id=user.id,
            service_id=service_id,
            start=start,
            client_name=user.full_name,
        )

        if not result["ok"]:
            await query.edit_message_text(
                f"❌ {result['error']}\n\nIltimos boshqa vaqt tanlang. /start"
            )
            return

        service = self.db.get_service(service_id)
        await query.edit_message_text(
            "✅ *Navbatingiz qabul qilindi!*\n\n"
            f"🔹 {service['name']}\n"
            f"🕒 {utils.format_datetime(start)}\n\n"
            "Belgilangan vaqtda kelishingizni so'raymiz. Rahmat! 🙏",
            parse_mode="Markdown",
        )

        # Holatni tozalaymiz
        context.user_data.clear()

        # Adminlarga xabar berish uchun ma'lumotni context.bot_data orqali
        # main.py da ulangan admin xabarnomasiga uzatamiz (ixtiyoriy).
        notify = context.bot_data.get("notify_admins")
        if notify:
            await notify(
                context,
                f"🆕 Yangi navbat!\n"
                f"👤 {user.full_name}\n"
                f"🔹 {service['name']}\n"
                f"🕒 {utils.format_datetime(start)}",
            )

    # ===============================================================
    # Mening navbatlarim + bekor qilish
    # ===============================================================

    async def my_bookings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        client = self.db.get_client_by_tg(user.id)
        if client is None:
            await update.message.reply_text("Sizda hali navbat yo'q. /start")
            return

        bookings = self.db.get_client_bookings(client["id"], only_active=True)
        # Faqat kelajakdagilarni ko'rsatamiz
        now = datetime.now()
        upcoming = [
            b for b in bookings
            if datetime.fromisoformat(b["start_time"]) > now
        ]

        if not upcoming:
            await update.message.reply_text(
                "Sizda faol navbat yo'q. 📭\n"
                "«📅 Navbat olish» tugmasi orqali yozilishingiz mumkin."
            )
            return

        await update.message.reply_text("Sizning navbatlaringiz:")
        for b in upcoming:
            start = datetime.fromisoformat(b["start_time"])
            text = (
                f"🔹 *{b['service_name']}*\n"
                f"🕒 {utils.format_datetime(start)}"
            )
            buttons = [[InlineKeyboardButton(
                "❌ Bekor qilish", callback_data=f"cancel:{b['id']}"
            )]]
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode="Markdown",
            )

    async def on_cancel_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        booking_id = int(query.data.split(":")[1])

        booking = self.db.get_booking(booking_id)
        user = update.effective_user
        client = self.db.get_client_by_tg(user.id)

        # Faqat o'z navbatini bekor qila olishini tekshiramiz
        if booking is None or client is None or booking["client_id"] != client["id"]:
            await query.answer("Bu navbat topilmadi.", show_alert=True)
            return

        self.db.cancel_booking(booking_id)
        await query.answer("Navbat bekor qilindi.")
        await query.edit_message_text("❌ Navbat bekor qilindi.")

    # ===============================================================
    # "Orqaga" tugmasi (xizmatlar ro'yxatiga qaytish)
    # ===============================================================

    async def on_back_to_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        services = self.db.get_services(only_active=True)
        buttons = [
            [InlineKeyboardButton(
                utils.service_label(s["name"], s["price"], s["duration"]),
                callback_data=f"svc:{s['id']}",
            )]
            for s in services
        ]
        await query.edit_message_text(
            "Qaysi xizmatga yozilmoqchisiz?",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
