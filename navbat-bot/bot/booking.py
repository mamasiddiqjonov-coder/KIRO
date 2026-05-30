"""
Bron mantiqi.

Bu modul "bo'sh vaqt" (slot) hisoblash bilan shug'ullanadi:
- berilgan kun uchun bo'sh vaqtlarni topadi (band bo'lganlarni chiqarib tashlaydi)
- yangi bron uchun vaqt bo'shligini tekshiradi
- bron qiladi (database orqali)

database.py'ga tayanadi, lekin Telegram'dan butunlay mustaqil.
Shuning uchun uni alohida test qilish oson.
"""

from datetime import datetime, timedelta, date, time

from .database import Database


class BookingManager:
    """Bo'sh vaqtlarni hisoblovchi va bron qiluvchi klass."""

    def __init__(
        self,
        db: Database,
        work_start_hour: int = 9,
        work_end_hour: int = 18,
        slot_minutes: int = 30,
        days_ahead: int = 7,
    ):
        self.db = db
        self.work_start_hour = work_start_hour
        self.work_end_hour = work_end_hour
        self.slot_minutes = slot_minutes
        self.days_ahead = days_ahead

    # ---------------------------------------------------------------
    # KUNLAR
    # ---------------------------------------------------------------

    def available_days(self, today: date | None = None) -> list[date]:
        """
        Bron qilish mumkin bo'lgan kunlarni qaytaradi (bugundan boshlab).
        days_ahead kun oldinga.
        """
        if today is None:
            today = date.today()
        return [today + timedelta(days=i) for i in range(self.days_ahead)]

    # ---------------------------------------------------------------
    # BO'SH VAQTLAR (SLOTLAR)
    # ---------------------------------------------------------------

    def _day_slots(self, day: date, duration: int) -> list[datetime]:
        """
        Bir kun ichidagi BARCHA mumkin bo'lgan slot boshlanish vaqtlari
        (bandligini hisobga olmasdan). Ish vaqti ichida.

        duration — xizmat davomiyligi (daqiqa). Slot tugashi ish vaqtidan
        oshmasligi kerak.
        """
        slots = []
        start = datetime.combine(day, time(hour=self.work_start_hour))
        work_end = datetime.combine(day, time(hour=self.work_end_hour))

        current = start
        step = timedelta(minutes=self.slot_minutes)
        dur = timedelta(minutes=duration)

        while current + dur <= work_end:
            slots.append(current)
            current += step
        return slots

    def get_free_slots(
        self, day: date, duration: int, now: datetime | None = None
    ) -> list[datetime]:
        """
        Bir kundagi BO'SH slotlarni qaytaradi.

        - band bo'lgan vaqtlar chiqarib tashlanadi (overlap tekshiruvi)
        - agar kun bugun bo'lsa, o'tib ketgan vaqtlar ko'rsatilmaydi
        """
        if now is None:
            now = datetime.now()

        dur = timedelta(minutes=duration)

        # Shu kundagi faol bronlarni bir marta o'qib olamiz
        day_start = datetime.combine(day, time(0, 0))
        day_end = datetime.combine(day, time(23, 59, 59))
        busy = self.db.get_active_bookings_in_range(day_start, day_end)

        # Band oraliqlarni datetime juftliklariga aylantiramiz
        busy_ranges = [
            (datetime.fromisoformat(b["start_time"]),
             datetime.fromisoformat(b["end_time"]))
            for b in busy
        ]

        free = []
        for slot_start in self._day_slots(day, duration):
            slot_end = slot_start + dur

            # O'tib ketgan vaqtni o'tkazib yuboramiz
            if slot_start <= now:
                continue

            # Band oraliq bilan kesishadimi?
            overlaps = any(
                slot_start < b_end and slot_end > b_start
                for b_start, b_end in busy_ranges
            )
            if not overlaps:
                free.append(slot_start)

        return free

    # ---------------------------------------------------------------
    # BRON QILISH
    # ---------------------------------------------------------------

    def is_slot_free(self, start: datetime, duration: int) -> bool:
        """
        Berilgan boshlanish vaqti hali ham bo'shmi? (bron qilishdan oldin
        oxirgi tekshiruv — bir vaqtda ikki kishi band qilib qo'ymasligi uchun)
        """
        end = start + timedelta(minutes=duration)
        overlap = self.db.get_active_bookings_in_range(start, end)
        return len(overlap) == 0

    def book(
        self, tg_id: int, service_id: int, start: datetime,
        client_name: str | None = None, client_phone: str | None = None,
    ) -> dict:
        """
        Bron qiladi.

        Qaytaradi: {"ok": True, "booking_id": int}  yoki
                   {"ok": False, "error": "sabab"}

        Bron qilishdan oldin:
        - xizmat mavjudligini tekshiradi
        - vaqt hali bo'shligini tekshiradi (poyga holatidan himoya)
        """
        service = self.db.get_service(service_id)
        if service is None or not service["is_active"]:
            return {"ok": False, "error": "Bunday xizmat topilmadi."}

        duration = service["duration"]
        end = start + timedelta(minutes=duration)

        if not self.is_slot_free(start, duration):
            return {"ok": False, "error": "Afsus, bu vaqt allaqachon band bo'lib qoldi."}

        client_id = self.db.get_or_create_client(
            tg_id, name=client_name, phone=client_phone
        )
        booking_id = self.db.create_booking(client_id, service_id, start, end)
        return {"ok": True, "booking_id": booking_id}
