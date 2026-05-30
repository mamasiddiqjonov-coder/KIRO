# 🚀 Botni ishga tushirish — qadamma-qadam

Bu qo'llanma bo'yicha botni o'z kompyuteringizda yoki serverda ishga tushirasiz.
Hech qanday oldindan tajriba shart emas — qadamlarni ketma-ket bajaring.

---

## 1️⃣ Telegram'da bot yaratish (token olish)

1. Telegram'da [@BotFather](https://t.me/BotFather) ni oching
2. `/newbot` deb yozing
3. Botga **nom** bering (masalan: `Salon Navbat`)
4. Botga **username** bering — `bot` bilan tugashi shart (masalan: `salon_navbat_bot`)
5. BotFather sizga **token** beradi. U shunday ko'rinadi:
   ```
   8123456789:AAH-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   👉 Bu tokenni nusxalab oling — keyin kerak bo'ladi.

---

## 2️⃣ O'z Telegram ID'ingizni bilib olish (admin bo'lish uchun)

1. Telegram'da [@userinfobot](https://t.me/userinfobot) ni oching
2. `/start` bosing
3. U sizga ID raqamingizni beradi (masalan: `123456789`)
   👉 Bu raqamni eslab qoling — siz bot egasi (admin) bo'lasiz.

---

## 3️⃣ Python o'rnatish (agar yo'q bo'lsa)

Kompyuteringizda Python 3.10+ bo'lishi kerak.

Tekshirish (terminal/buyruq satrida):
```bash
python --version
```
Agar `Python 3.10` yoki undan yuqori chiqsa — yaxshi.
Agar yo'q bo'lsa: [python.org/downloads](https://www.python.org/downloads/) dan yuklab oling.

> Windows'da o'rnatishda **"Add Python to PATH"** belgisini albatta belgilang!

---

## 4️⃣ Loyihani sozlash

Terminal/buyruq satrini oching va loyiha papkasiga kiring:
```bash
cd navbat-bot
```

**a) Kerakli kutubxonani o'rnating:**
```bash
pip install -r requirements.txt
```

**b) Sozlama faylini tayyorlang:**

`config.example.py` faylidan nusxa oling va nomini `config.py` qiling:

- **Windows:**
  ```bash
  copy config.example.py config.py
  ```
- **Mac / Linux:**
  ```bash
  cp config.example.py config.py
  ```

**c) `config.py` ni tahrirlang** (oddiy matn muharririda oching) va shularni o'zgartiring:
```python
BOT_TOKEN = "8123456789:AAH-..."   # 1-qadamdagi token
ADMIN_IDS = [123456789]            # 2-qadamdagi sizning ID
BUSINESS_NAME = "Mening Salonim"   # biznesingiz nomi
WORK_START_HOUR = 9                # ish boshlanishi
WORK_END_HOUR = 18                 # ish tugashi
```

---

## 5️⃣ (Ixtiyoriy) Namuna xizmatlar qo'shish

Sinab ko'rish uchun tayyor xizmatlar qo'shishingiz mumkin:
```bash
python seed.py
```
Yoki bu qadamni o'tkazib yuborib, xizmatlarni bot ichida
«➕ Xizmat qo'shish» tugmasi orqali qo'shasiz.

---

## 6️⃣ Botni ishga tushirish 🎉

```bash
python main.py
```

Terminalda `Bot ishga tushdi` degan yozuv chiqsa — tayyor!
Endi Telegram'da o'z botingizni oching va `/start` bosing.

**To'xtatish uchun:** terminalda `Ctrl + C` bosing.

---

## 📱 Qanday ishlatiladi?

### Mijoz uchun:
- `/start` → asosiy menyu
- **📅 Navbat olish** → xizmat → kun → vaqt → tasdiqlash
- **📋 Mening navbatlarim** → navbatlarni ko'rish va bekor qilish

### Egasi (admin) uchun:
- `/admin` → boshqaruv paneli
- **📅 Bugungi navbatlar** / **📆 Ertangi navbatlar**
- **🛠 Xizmatlar** → ko'rish va o'chirish
- **➕ Xizmat qo'shish** → yangi xizmat (nom → narx → davomiylik)
- **📊 Statistika**

Yangi navbat kelganda, adminga avtomatik xabar keladi. ✅

---

## ❓ Tez-tez uchraydigan muammolar

**"ModuleNotFoundError: No module named 'telegram'"**
→ `pip install -r requirements.txt` ni qayta bajaring.

**"ModuleNotFoundError: No module named 'config'"**
→ `config.py` faylini yaratmadingiz (4-qadam, b bo'limi).

**"Unauthorized" yoki token xatosi**
→ `config.py` dagi `BOT_TOKEN` noto'g'ri. BotFather'dan qayta tekshiring.

**Admin tugmalari ishlamayapti**
→ `config.py` dagi `ADMIN_IDS` ga o'z ID'ingizni to'g'ri yozganingizni tekshiring.

---

## 🌐 Doimiy ishlashi uchun (server)

Kompyuteringizni o'chirsangiz, bot ham to'xtaydi. Bot doim ishlab turishi uchun
arzon server (VPS) ijaraga olishingiz mumkin. Buni keyingi bosqichda
birga sozlashimiz mumkin (masalan systemd xizmati sifatida).
```bash
# Server uchun namuna (keyinroq batafsil ko'rsataman)
nohup python main.py &
```
