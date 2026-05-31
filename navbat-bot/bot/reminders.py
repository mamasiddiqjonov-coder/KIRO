"""
Eslatma tizimi.

Bot belgilangan vaqtda (masalan har 5 daqiqada) bazani tekshiradi va
yaqinlashayotgan navbatlar uchun mijozlarga avtomatik eslatma yuboradi.

Bu "no-show" (kelmay qolish) muammosini kamaytiradi — biznes uchun
eng qimmatli funksiya, chunki bo'sh ketgan vaqt = yo'qolgan pul.

main.py da JobQueue orqali ulanadi.
"""

import logging
from datetime import datetime, timedelta

from telegram.ext import ContextTypes

from .database import Database
from . import utils

logger = logging.getLogger(__name__)


class ReminderService:
    """Yaqinlashayotgan navbatlar uchun eslatma yuboruvchi."""

    def __init__(self, db: Database, business_name: str, lead_minutes: int = 60):
        """
        db            — ma'lumotlar bazasi
        business_name — biznes nomi (xabarda ko'rsatiladi)
        lead_minutes  — navbatdan necha daqiqa oldin eslatish (standart: 60)
        """
        self.db = db
        self.business_name = business_name
        self.lead_minutes = lead_minutes

    async def check_and_send(self, context: ContextTypes.DEFAULT_TYPE):
        """
        JobQueue chaqiradigan funksiya. Eslatma vaqti kelgan bronlarni topadi
        va har biriga xabar yuboradi.
        """
        now = datetime.now()
        until = now + timedelta(minutes=self.lead_minutes)

        bookings = self.db.get_bookings_to_remind(now, until)
        if not bookings:
            return

        for b in bookings:
            start = datetime.fromisoformat(b["start_time"])
            tg_id = b["client_tg"]

            # Navbatga qancha qoldi (daqiqada)
            minutes_left = int((start - now).total_seconds() // 60)

            text = (
                "🔔 *Eslatma!*\n\n"
                f"Sizning navbatingiz yaqinlashdi:\n"
                f"🔹 {b['service_name']}\n"
                f"🕒 {utils.format_datetime(start)}\n"
                f"⏳ Taxminan {minutes_left} daqiqadan so'ng\n\n"
                f"*{self.business_name}* sizni kutadi! 🙏"
            )

            try:
                await context.bot.send_message(
                    chat_id=tg_id, text=text, parse_mode="Markdown"
                )
                # Yuborilgach belgilaymiz (qayta yubormaslik uchun)
                self.db.mark_reminded(b["id"])
                logger.info("Eslatma yuborildi: bron #%s -> tg %s", b["id"], tg_id)
            except Exception as e:
                # Mijoz botni bloklagan bo'lishi mumkin — xato bo'lsa ham bot to'xtamaydi
                logger.warning(
                    "Eslatma yuborilmadi (bron #%s, tg %s): %s", b["id"], tg_id, e
                )
