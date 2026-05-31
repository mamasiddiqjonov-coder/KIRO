# Navbat Bot 🤖

Telegram orqali **navbat / bron** qabul qiluvchi bot. Sartaroshxona, klinika, repetitor, fotograf, kafe va boshqa xizmat ko'rsatuvchilar uchun.

## Nima qiladi?

**Mijoz uchun:**
- Xizmatni tanlaydi (masalan: "Soch olish", "Soqol olish")
- Bo'sh kun va vaqtni tanlaydi
- Bron qiladi va tasdiqlash oladi
- O'z bronlarini ko'radi va bekor qila oladi
- Telefon raqamini qoldiradi (egasi bog'lana olishi uchun)
- Navbatdan oldin avtomatik **eslatma** oladi 🔔

**Egasi (admin) uchun:**
- Barcha bronlarni ko'radi (mijoz ismi va telefoni bilan)
- Yangi xizmat qo'shadi / o'chiradi
- Bugungi navbatlarni ko'radi
- Yangi bron kelganda darhol xabar oladi

## Texnologiya

- Python 3.11+
- python-telegram-bot (JobQueue bilan — eslatmalar uchun)
- SQLite (alohida server kerak emas)

## O'rnatish

Pastdagi `ISHGA_TUSHIRISH.md` faylida qadamma-qadam ko'rsatma bor.

## Struktura

```
navbat-bot/
├── bot/
│   ├── database.py     # Ma'lumotlar bazasi (xizmatlar, bronlar, mijozlar)
│   ├── booking.py      # Bron mantiqi (bo'sh vaqtlar, band qilish)
│   ├── handlers.py     # Telegram tugmalar va xabarlar (mijoz)
│   ├── admin.py        # Egasi uchun buyruqlar
│   ├── reminders.py    # Avtomatik eslatma tizimi
│   └── utils.py        # Sana/narx formatlash
├── main.py             # Botni ishga tushiruvchi fayl
├── config.example.py   # Sozlamalar namunasi
├── seed.py             # Namuna xizmatlar
├── requirements.txt
└── README.md
```
