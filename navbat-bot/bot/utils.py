"""
Yordamchi funksiyalar: o'zbekcha sana/vaqt formatlash, narx ko'rinishi.
Telegram'dan mustaqil — alohida test qilsa bo'ladi.
"""

from datetime import date, datetime


# O'zbekcha hafta kunlari (Monday=0)
WEEKDAYS_UZ = [
    "Dushanba", "Seshanba", "Chorshanba", "Payshanba",
    "Juma", "Shanba", "Yakshanba",
]

# O'zbekcha oylar (1-indeksli ishlatish uchun bo'sh element bilan)
MONTHS_UZ = [
    "", "yanvar", "fevral", "mart", "aprel", "may", "iyun",
    "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr",
]


def format_day(d: date, today: date | None = None) -> str:
    """
    Sanani chiroyli ko'rsatadi.
    Bugun/Ertaga bo'lsa shunday yozadi, aks holda: "Dushanba, 2 iyun".
    """
    if today is None:
        today = date.today()

    delta = (d - today).days
    weekday = WEEKDAYS_UZ[d.weekday()]
    base = f"{weekday}, {d.day} {MONTHS_UZ[d.month]}"

    if delta == 0:
        return f"Bugun ({base})"
    if delta == 1:
        return f"Ertaga ({base})"
    return base


def format_time(dt: datetime) -> str:
    """Vaqtni HH:MM ko'rinishida qaytaradi."""
    return dt.strftime("%H:%M")


def format_datetime(dt: datetime, today: date | None = None) -> str:
    """To'liq: 'Ertaga (Seshanba, 2 iyun) 14:30' ko'rinishida."""
    return f"{format_day(dt.date(), today)} {format_time(dt)}"


def format_price(price: int) -> str:
    """
    Narxni chiroyli ko'rsatadi: 40000 -> "40 000 so'm".
    0 bo'lsa narx ko'rsatilmaydi.
    """
    if not price:
        return ""
    # Mingliklarni probel bilan ajratamiz
    s = f"{price:,}".replace(",", " ")
    return f"{s} so'm"


def service_label(name: str, price: int, duration: int) -> str:
    """
    Xizmat tugmasi uchun yorliq:
    "Soch olish — 40 000 so'm · 30 daq"
    """
    parts = [name]
    p = format_price(price)
    extra = []
    if p:
        extra.append(p)
    extra.append(f"{duration} daq")
    if extra:
        parts.append(" · ".join(extra))
    return " — ".join(parts)
