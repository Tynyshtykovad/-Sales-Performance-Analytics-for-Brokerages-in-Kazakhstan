import sqlite3
import pandas as pd

conn = sqlite3.connect("bitrix.db")

print("\n📌 Таблица managers:")
print(pd.read_sql("SELECT * FROM managers", conn))

print("\n📌 Таблица deals:")
print(pd.read_sql("SELECT * FROM deals", conn))

conn.close()

