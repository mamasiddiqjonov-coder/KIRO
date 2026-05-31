"""
Namuna xizmatlar qo'shish (ixtiyoriy).

Botni birinchi marta sinab ko'rishda bazada xizmat bo'lishi uchun.
Ishlatish:  python seed.py

Eslatma: o'z biznesingizga moslab xizmatlarni o'zgartiring yoki bot ichida
«➕ Xizmat qo'shish» orqali qo'shing.
"""

import config
from bot.database import Database

# Namuna xizmatlar: (nom, narx, davomiylik daqiqada)
# Narx erkin matn: toza raqam yozsangiz bot chiroyli qiladi ("40000" -> "40 000 so'm"),
# yoki o'zingiz belgili yozasiz ("от 30 000", "Kelishiladi" va h.k.)
SAMPLE_SERVICES = [
    ("Soch olish", "40000", 30),
    ("Soqol olish", "20000", 20),
    ("Soch + soqol", "55 000 so'm", 45),
    ("Bolalar sochi", "от 30 000", 25),
]


def main():
    db = Database(config.DB_PATH)
    existing = db.get_services(only_active=True)
    if existing:
        print(f"Bazada allaqachon {len(existing)} ta xizmat bor. "
              "Namuna qo'shilmadi.")
        return

    for name, price, duration in SAMPLE_SERVICES:
        sid = db.add_service(name, price=price, duration=duration)
        print(f"  + qo'shildi: {name} (id={sid})")

    print(f"\n✅ {len(SAMPLE_SERVICES)} ta namuna xizmat qo'shildi.")


if __name__ == "__main__":
    main()
