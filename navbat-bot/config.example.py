"""
Bot sozlamalari (namuna fayli).

Ishlatish:
1. Bu faylni nusxalang va nomini "config.py" qiling.
2. BOT_TOKEN ga BotFather bergan tokenni qo'ying.
3. ADMIN_IDS ga egasining Telegram ID raqamini qo'ying.

DIQQAT: config.py faylini hech kimga bermang va GitHub'ga yuklamang!
(u .gitignore ichida himoyalangan)
"""

# BotFather'dan olingan token (masalan: "123456789:AAH...")
BOT_TOKEN = "BU_YERGA_TOKEN_QOYING"

# Bot egasining Telegram ID'lari (raqam).
# O'z ID'ingizni @userinfobot dan bilib olasiz.
ADMIN_IDS = [123456789]

# Biznes nomi (mijozlarga ko'rinadi)
BUSINESS_NAME = "Mening Biznesim"

# Ish vaqti (soatlarda, 24 soatlik format)
WORK_START_HOUR = 9    # 09:00
WORK_END_HOUR = 18     # 18:00

# Har bir bron uchun standart davomiylik (daqiqada) — agar xizmatda alohida belgilanmagan bo'lsa
DEFAULT_SLOT_MINUTES = 30

# Necha kun oldindan bron qilish mumkin
BOOKING_DAYS_AHEAD = 7

# Ma'lumotlar bazasi fayli
DB_PATH = "navbat.db"
