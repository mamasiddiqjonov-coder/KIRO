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


def format_price(price) -> str:
    """
    Narxni chiroyli ko'rsatadi.

    - Bo'sh bo'lsa ("", 0, None) -> "" (narx ko'rsatilmaydi)
    - Toza raqam bo'lsa: "40000" yoki 40000 -> "40 000 so'm"
    - Matn/belgili bo'lsa: "от 30 000", "$20", "Kelishiladi" -> o'zgartirilmasdan
    """
    if price is None:
        return ""

    s = str(price).strip()
    if not s or s == "0":
        return ""

    # Toza raqammi? (faqat raqam va probellardan iborat, masalan "40000" yoki "40 000")
    digits_only = s.replace(" ", "")
    if digits_only.isdigit():
        n = int(digits_only)
        if n == 0:
            return ""
        pretty = f"{n:,}".replace(",", " ")
        return f"{pretty} so'm"

    # Aks holda — admin nima yozgan bo'lsa, shuni qoldiramiz (belgilar saqlanadi)
    return s


def service_label(name: str, price, duration: int) -> str:
    """
    Xizmat tugmasi uchun yorliq:
    "Soch olish — 40 000 so'm · 30 daq"
    price — son yoki matn bo'lishi mumkin.
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
