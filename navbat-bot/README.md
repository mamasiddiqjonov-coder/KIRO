# Navbat Bot 🤖

Telegram orqali **navbat / bron** qabul qiluvchi bot. Sartaroshxona, klinika, repetitor, fotograf, kafe va boshqa xizmat ko'rsatuvchilar uchun.

## Nima qiladi?

**Mijoz uchun:**
- Xizmatni tanlaydi (masalan: "Soch olish", "Soqol olish")
- Bo'sh kun va vaqtni tanlaydi
- Bron qiladi va tasdiqlash oladi
- O'z bronlarini ko'radi va bekor qila oladi

**Egasi (admin) uchun:**
- Barcha bronlarni ko'radi
- Yangi xizmat qo'shadi / o'chiradi
- Bugungi navbatlarni ko'radi

## Texnologiya

- Python 3.11+
- python-telegram-bot
- SQLite (alohida server kerak emas)

## O'rnatish

Pastdagi `ISHGA_TUSHIRISH.md` faylida qadamma-qadam ko'rsatma bor.

## Struktura

```
navbat-bot/
├── bot/
│   ├── database.py     # Ma'lumotlar bazasi (xizmatlar, bronlar)
│   ├── booking.py      # Bron mantiqi (bo'sh vaqtlar, band qilish)
│   ├── handlers.py     # Telegram tugmalar va xabarlar
│   └── admin.py        # Egasi uchun buyruqlar
├── main.py             # Botni ishga tushiruvchi fayl
├── config.example.py   # Sozlamalar namunasi
├── requirements.txt
└── README.md
```
