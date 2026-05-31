"""
Admin (biznes egasi) paneli.

Egasi qila oladigan ishlar:
  /admin              -> admin menyusi
  Bugungi navbatlar   -> bugungi faol navbatlar ro'yxati
  Ertangi navbatlar   -> ertangi navbatlar
  Xizmatlar           -> xizmatlar ro'yxati + o'chirish
  Xizmat qo'shish     -> suhbat orqali yangi xizmat (nom -> narx -> davomiylik)
  Statistika          -> umumiy raqamlar

Faqat config.ADMIN_IDS dagi foydalanuvchilar kira oladi.
"""

from datetime import date, datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from .database import Database
from . import utils


# Xizmat qo'shish suhbatining bosqichlari
ADD_NAME, ADD_PRICE, ADD_DURATION = range(3)


# Admin menyusi (pastdagi klaviatura)
ADMIN_KB = ReplyKeyboardMarkup(
    [
        ["📅 Bugungi navbatlar", "📆 Ertangi navbatlar"],
        ["🛠 Xizmatlar", "➕ Xizmat qo'shish"],
        ["📊 Statistika"],
    ],
    resize_keyboard=True,
)


class AdminHandlers:
    """Egasi buyruqlarini boshqaruvchi klass."""

    def __init__(self, db: Database, admin_ids: list[int], business_name: str):
        self.db = db
        self.admin_ids = set(admin_ids)
        self.business_name = business_name

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    async def _deny(self, update: Update) -> bool:
        """Admin emas bo'lsa True qaytaradi (va xabar beradi)."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("Bu bo'lim faqat egasi uchun. ⛔")
            return True
        return False

    # ===============================================================
    # /admin
    # ===============================================================

    async def admin_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self._deny(update):
            return
        await update.message.reply_text(
            f"*{self.business_name}* — boshqaruv paneli 👨‍💼",
            reply_markup=ADMIN_KB,
            parse_mode="Markdown",
        )

    # ===============================================================
    # Navbatlarni ko'rish
    # ===============================================================

    async def _show_day_bookings(self, update: Update, day: date, title: str):
        bookings = self.db.get_bookings_for_day(datetime.combine(day, datetime.min.time()))
        if not bookings:
            await update.message.reply_text(f"{title}: navbat yo'q. 📭")
            return

        lines = [f"*{title}* ({utils.format_day(day)}):\n"]
        for b in bookings:
            start = datetime.fromisoformat(b["start_time"])
            phone = b["client_phone"] or "—"
            lines.append(
                f"🕒 {utils.format_time(start)} — {b['service_name']}\n"
                f"   👤 {b['client_name']}  ({phone})"
            )
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def today_bookings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self._deny(update):
            return
        await self._show_day_bookings(update, date.today(), "Bugungi navbatlar")

    async def tomorrow_bookings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self._deny(update):
            return
        await self._show_day_bookings(
            update, date.today() + timedelta(days=1), "Ertangi navbatlar"
        )

    # ===============================================================
    # Xizmatlar ro'yxati + o'chirish
    # ===============================================================

    async def list_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self._deny(update):
            return
        services = self.db.get_services(only_active=True)
        if not services:
            await update.message.reply_text(
                "Hozircha xizmat yo'q. «➕ Xizmat qo'shish» orqali qo'shing."
            )
            return

        await update.message.reply_text("Xizmatlar (o'chirish uchun tugmani bosing):")
        for s in services:
            label = utils.service_label(s["name"], s["price"], s["duration"])
            buttons = [[InlineKeyboardButton(
                "🗑 O'chirish", callback_data=f"delsvc:{s['id']}"
            )]]
            await update.message.reply_text(
                label, reply_markup=InlineKeyboardMarkup(buttons)
            )

    async def on_delete_service(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not self.is_admin(update.effective_user.id):
            await query.answer("Ruxsat yo'q.", show_alert=True)
            return
        service_id = int(query.data.split(":")[1])
        self.db.deactivate_service(service_id)
        await query.answer("Xizmat o'chirildi.")
        await query.edit_message_text("🗑 Xizmat o'chirildi.")

    # ===============================================================
    # Statistika
    # ===============================================================

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self._deny(update):
            return

        today = date.today()
        today_count = len(
            self.db.get_bookings_for_day(datetime.combine(today, datetime.min.time()))
        )

        # Kelgusi 7 kun bo'yicha jami navbat
        week_count = 0
        for i in range(7):
            d = today + timedelta(days=i)
            week_count += len(
                self.db.get_bookings_for_day(datetime.combine(d, datetime.min.time()))
            )

        services = self.db.get_services(only_active=True)

        text = (
            "📊 *Statistika*\n\n"
            f"📅 Bugungi navbatlar: *{today_count}*\n"
            f"📆 Kelgusi 7 kun: *{week_count}*\n"
            f"🛠 Faol xizmatlar: *{len(services)}*"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    # ===============================================================
    # Xizmat qo'shish (ConversationHandler)
    # ===============================================================

    async def add_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self._deny(update):
            return ConversationHandler.END
        await update.message.reply_text(
            "Yangi xizmat nomini kiriting:\n(bekor qilish uchun /bekor)"
        )
        return ADD_NAME

    async def add_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        name = update.message.text.strip()
        if not name:
            await update.message.reply_text("Nom bo'sh bo'lmasin. Qaytadan kiriting:")
            return ADD_NAME
        context.user_data["new_name"] = name
        await update.message.reply_text(
            f"«{name}» narxini kiriting.\n\n"
            "Masalan: 40000  yoki  50 000 so'm  yoki  от 30 000  yoki  $20\n"
            "Narx bo'lmasa yoki yozmoqchi bo'lmasangiz «-» (chiziqcha) kiriting:"
        )
        return ADD_PRICE

    async def add_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip()
        # «-» yoki «0» -> narxsiz
        if text in ("-", "0", "—"):
            text = ""
        # Narx erkin matn: belgilar, valyuta, "Kelishiladi" — hammasi mumkin.
        # Faqat juda uzun bo'lib ketmasligi uchun cheklov qo'yamiz.
        if len(text) > 50:
            await update.message.reply_text(
                "Narx juda uzun (50 belgidan oshmasin). Qaytadan kiriting:"
            )
            return ADD_PRICE
        context.user_data["new_price"] = text
        await update.message.reply_text(
            "Xizmat necha daqiqa davom etadi? (masalan: 30)"
        )
        return ADD_DURATION

    async def add_duration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip()
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text(
                "Davomiylik musbat raqam bo'lsin (daqiqada). Qaytadan:"
            )
            return ADD_DURATION

        name = context.user_data["new_name"]
        price = context.user_data["new_price"]
        duration = int(text)

        self.db.add_service(name, price=price, duration=duration)
        await update.message.reply_text(
            "✅ Xizmat qo'shildi:\n"
            f"{utils.service_label(name, price, duration)}",
            reply_markup=ADMIN_KB,
        )
        context.user_data.clear()
        return ConversationHandler.END

    async def add_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.message.reply_text(
            "Bekor qilindi.", reply_markup=ADMIN_KB
        )
        return ConversationHandler.END
