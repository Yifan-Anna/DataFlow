from __future__ import annotations

import sqlite3
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent
DATABASE_PATH = DATA_DIR / "ecommerce.db"


def ensure_database(database_path: Path = DATABASE_PATH) -> dict[str, int | float]:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                pay_amount REAL NOT NULL CHECK (pay_amount >= 0),
                pay_status TEXT NOT NULL CHECK (pay_status IN ('SUCCESS', 'FAILED')),
                channel TEXT NOT NULL,
                region TEXT NOT NULL,
                pay_time TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_orders_status_time ON orders(pay_status, pay_time)"
        )
        row_count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        if row_count != 600:
            connection.execute("DELETE FROM orders")
            connection.executemany(
                """
                INSERT INTO orders (
                    order_id, user_id, product_id, pay_amount,
                    pay_status, channel, region, pay_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                list(_build_orders()),
            )
        connection.execute("PRAGMA optimize")
        september_gmv = connection.execute(
            """SELECT SUM(pay_amount) FROM orders
               WHERE pay_status = 'SUCCESS'
               AND pay_time >= '2026-09-01' AND pay_time < '2026-10-01'"""
        ).fetchone()[0]
        september_orders = connection.execute(
            """SELECT COUNT(DISTINCT order_id) FROM orders
               WHERE pay_status = 'SUCCESS'
               AND pay_time >= '2026-09-01' AND pay_time < '2026-10-01'"""
        ).fetchone()[0]
    return {
        "row_count": 600,
        "september_gmv": september_gmv,
        "september_orders": september_orders,
    }


def _build_orders():
    channels = ("自然流量", "直播", "广告", "私域")
    regions = ("华北", "华东", "华南", "西南")
    order_number = 1
    month_specs = (
        (8, 200, 40, 500.0),
        (9, 200, 40, 600.0),
        (10, 100, 20, 550.0),
    )
    for month, success_count, failed_count, amount in month_specs:
        for index in range(success_count + failed_count):
            status = "SUCCESS" if index < success_count else "FAILED"
            day = index % 28 + 1
            hour = index % 24
            yield (
                f"ORD{order_number:06d}",
                f"USR{index % 160 + 1:04d}",
                f"SKU{index % 48 + 1:03d}",
                amount,
                status,
                channels[index % len(channels)],
                regions[index % len(regions)],
                f"2026-{month:02d}-{day:02d} {hour:02d}:00:00",
            )
            order_number += 1


if __name__ == "__main__":
    print(ensure_database())
