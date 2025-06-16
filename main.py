# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from fastapi import FastAPI
from bitrix_client import get_profile, get_deals

app = FastAPI()

@app.get("/api/profile")
def profile():
    return get_profile()

@app.get("/api/deals")
def deals():
    return get_deals()
