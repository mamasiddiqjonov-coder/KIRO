"""
Ma'lumotlar bazasi qatlami (SQLite).

Bu modul faqat ma'lumotlarni saqlash/o'qish bilan shug'ullanadi.
Bron mantiqi (bo'sh vaqt tekshirish) booking.py da.

Jadvallar:
- services : xizmatlar (nomi, narxi, davomiyligi daqiqada)
- clients  : mijozlar (telegram id, ism, telefon)
- bookings : bronlar (mijoz, xizmat, sana-vaqt, holat)
"""

import sqlite3
from datetime import datetime
from contextlib import contextmanager


# Bron holatlari
STATUS_ACTIVE = "active"        # faol bron
STATUS_CANCELLED = "cancelled"  # bekor qilingan
STATUS_DONE = "done"            # bajarilgan


class Database:
    """SQLite bilan ishlovchi asosiy klass."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_tables()

    @contextmanager
    def _connect(self):
        """
        Har bir amal uchun ulanish ochib-yopadigan kontekst menejer.
        row_factory=Row -> natijalarni ustun nomi bilan o'qiymiz (qator['nomi']).
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Tashqi kalitlarni (foreign key) yoqamiz
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_tables(self):
        """Jadvallar mavjud bo'lmasa, yaratadi."""
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS services (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT    NOT NULL,
                    price       INTEGER NOT NULL DEFAULT 0,
                    duration    INTEGER NOT NULL DEFAULT 30,
                    is_active   INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS clients (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_id       INTEGER NOT NULL UNIQUE,
                    name        TEXT,
                    phone       TEXT,
                    created_at  TEXT    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS bookings (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id   INTEGER NOT NULL,
                    service_id  INTEGER NOT NULL,
                    start_time  TEXT    NOT NULL,
                    end_time    TEXT    NOT NULL,
                    status      TEXT    NOT NULL DEFAULT 'active',
                    created_at  TEXT    NOT NULL,
                    FOREIGN KEY (client_id)  REFERENCES clients(id),
                    FOREIGN KEY (service_id) REFERENCES services(id)
                );
                """
            )

    # ---------------------------------------------------------------
    # XIZMATLAR (services)
    # ---------------------------------------------------------------

    def add_service(self, name: str, price: int = 0, duration: int = 30) -> int:
        """Yangi xizmat qo'shadi. Qo'shilgan xizmat id'sini qaytaradi."""
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO services (name, price, duration) VALUES (?, ?, ?)",
                (name, price, duration),
            )
            return cur.lastrowid

    def get_services(self, only_active: bool = True) -> list[sqlite3.Row]:
        """Xizmatlar ro'yxatini qaytaradi."""
        with self._connect() as conn:
            if only_active:
                rows = conn.execute(
                    "SELECT * FROM services WHERE is_active = 1 ORDER BY id"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM services ORDER BY id"
                ).fetchall()
            return rows

    def get_service(self, service_id: int) -> sqlite3.Row | None:
        """Bitta xizmatni id bo'yicha qaytaradi."""
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM services WHERE id = ?", (service_id,)
            ).fetchone()

    def deactivate_service(self, service_id: int) -> None:
        """Xizmatni o'chirmasdan nofaol qiladi (eski bronlar saqlanib qoladi)."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE services SET is_active = 0 WHERE id = ?", (service_id,)
            )

    # ---------------------------------------------------------------
    # MIJOZLAR (clients)
    # ---------------------------------------------------------------

    def get_or_create_client(
        self, tg_id: int, name: str | None = None, phone: str | None = None
    ) -> int:
        """
        Mijozni topadi, bo'lmasa yaratadi. client.id qaytaradi.
        Ism/telefon berilgan bo'lsa yangilaydi.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM clients WHERE tg_id = ?", (tg_id,)
            ).fetchone()

            if row is None:
                cur = conn.execute(
                    "INSERT INTO clients (tg_id, name, phone, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (tg_id, name, phone, datetime.now().isoformat()),
                )
                return cur.lastrowid

            # Mavjud bo'lsa va yangi ma'lumot kelsa — yangilaymiz
            if name is not None or phone is not None:
                conn.execute(
                    "UPDATE clients SET "
                    "name = COALESCE(?, name), "
                    "phone = COALESCE(?, phone) "
                    "WHERE id = ?",
                    (name, phone, row["id"]),
                )
            return row["id"]

    def get_client_by_tg(self, tg_id: int) -> sqlite3.Row | None:
        """Mijozni telegram id bo'yicha qaytaradi."""
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM clients WHERE tg_id = ?", (tg_id,)
            ).fetchone()

    # ---------------------------------------------------------------
    # BRONLAR (bookings)
    # ---------------------------------------------------------------

    def create_booking(
        self,
        client_id: int,
        service_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        """Yangi bron yaratadi. Bron id'sini qaytaradi."""
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO bookings "
                "(client_id, service_id, start_time, end_time, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    client_id,
                    service_id,
                    start_time.isoformat(),
                    end_time.isoformat(),
                    STATUS_ACTIVE,
                    datetime.now().isoformat(),
                ),
            )
            return cur.lastrowid

    def get_active_bookings_in_range(
        self, start: datetime, end: datetime
    ) -> list[sqlite3.Row]:
        """
        Berilgan vaqt oralig'idagi FAOL bronlarni qaytaradi.
        Bo'sh vaqtlarni hisoblashda ishlatiladi.
        """
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM bookings "
                "WHERE status = ? AND start_time < ? AND end_time > ? "
                "ORDER BY start_time",
                (STATUS_ACTIVE, end.isoformat(), start.isoformat()),
            ).fetchall()

    def get_client_bookings(
        self, client_id: int, only_active: bool = True
    ) -> list[sqlite3.Row]:
        """Bitta mijozning bronlarini xizmat nomi bilan birga qaytaradi."""
        with self._connect() as conn:
            query = (
                "SELECT b.*, s.name AS service_name, s.price AS service_price "
                "FROM bookings b "
                "JOIN services s ON s.id = b.service_id "
                "WHERE b.client_id = ? "
            )
            params = [client_id]
            if only_active:
                query += "AND b.status = ? "
                params.append(STATUS_ACTIVE)
            query += "ORDER BY b.start_time"
            return conn.execute(query, params).fetchall()

    def get_bookings_for_day(self, day: datetime) -> list[sqlite3.Row]:
        """
        Bir kundagi barcha faol bronlarni qaytaradi (admin uchun).
        Mijoz ismi va xizmat nomi bilan birga.
        """
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start.replace(hour=23, minute=59, second=59)
        with self._connect() as conn:
            return conn.execute(
                "SELECT b.*, s.name AS service_name, "
                "c.name AS client_name, c.phone AS client_phone, c.tg_id AS client_tg "
                "FROM bookings b "
                "JOIN services s ON s.id = b.service_id "
                "JOIN clients c ON c.id = b.client_id "
                "WHERE b.status = ? AND b.start_time >= ? AND b.start_time <= ? "
                "ORDER BY b.start_time",
                (STATUS_ACTIVE, day_start.isoformat(), day_end.isoformat()),
            ).fetchall()

    def get_booking(self, booking_id: int) -> sqlite3.Row | None:
        """Bitta bronni id bo'yicha qaytaradi."""
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM bookings WHERE id = ?", (booking_id,)
            ).fetchone()

    def cancel_booking(self, booking_id: int) -> None:
        """Bronni bekor qiladi (holatini o'zgartiradi)."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE bookings SET status = ? WHERE id = ?",
                (STATUS_CANCELLED, booking_id),
            )
