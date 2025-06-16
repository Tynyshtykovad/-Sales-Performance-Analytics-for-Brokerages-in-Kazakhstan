from models import Manager, Deal
from database import SessionLocal
from dotenv import load_dotenv
import os
import requests

load_dotenv()

BASE_URL = os.getenv("BITRIX_WEBHOOK_BASE")

def get_profile():
    url = f"{BASE_URL}/profile.json"
    return requests.get(url).json()

def get_deals():
    url = f"{BASE_URL}/crm.deal.list.json"
    return requests.get(url).json()

# ✅ ЭТА ФУНКЦИЯ загружает данные в базу
async def sync_data():
    from database import SessionLocal
    async with SessionLocal() as session:
        profile = get_profile().get("result")
        deals = get_deals().get("result", [])

        manager = Manager(
            id=int(profile["ID"]),
            name=profile["NAME"],
            last_name=profile["LAST_NAME"],
            is_admin=profile["ADMIN"]
        )
        session.add(manager)

        for d in deals:
            deal = Deal(
                id=int(d["ID"]),
                title=d["TITLE"],
                type_id=d["TYPE_ID"],
                stage_id=d["STAGE_ID"],
                currency_id=d["CURRENCY_ID"],
                opportunity=float(d["OPPORTUNITY"]),
                begindate=d["BEGINDATE"],
                closedate=d["CLOSEDATE"],
                assigned_by_id=int(d["ASSIGNED_BY_ID"]),
                date_create=d["DATE_CREATE"],
                date_modify=d["DATE_MODIFY"],
                source_id=d["SOURCE_ID"],
                last_activity_time=d["LAST_ACTIVITY_TIME"]
            )
            session.add(deal)

        await session.commit()
