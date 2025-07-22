from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("api_key")
client = genai.Client(api_key=api_key)
model_name = "gemini-2.0-flash"

def get_product_price(product_name):
    prompt = f"Menga {product_name} mahsulotining O'zbekistondagi o'rtacha joriy narxini UZSda aytib ber. Faqatgina raqamli narx raqam ko'rinishida ko'rsatilgan holda ayt."
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    price_text = response.text.strip()
    return {product_name: price_text}

def get_sort_csv(csv_text):
    print("CSV matni:", csv_text)
    prompt = (
        "Quyida rasm yoki PDF fayldan chiqarilgan, noto'g'ri tuzilgan CSV jadvali berilgan.\n"
        "Jadvaldagi ustunlar siljigan, ba'zi qiymatlar noto‘g‘ri qatorlarga tushib qolgan, yoki bitta katakdagi ma'lumotlar bir nechtaga bo‘lingan.\n\n"
        "Sizdan quyidagilarni so‘rayman:\n"
        "- Jadvaldagi mahsulot nomlarini aniqlang.\n"
        "- Har bir mahsulotga mos ravishda uning 'bir birlik uchun qiymati' ni aniqlang.\n"
        "- Natijani quyidagi shaklda lug'at (dictionary) ko‘rinishida qaytaring: {mahsulot_nomi: bir birlik uchun qiymati}\n\n"
        "Mana CSV matni:\n\n"
        f"{csv_text}\n\n"
        "‼️ Iltimos, faqat va faqat tayyor lug'atni (dictionary) qaytaring, boshqa hech qanday izoh, matn yoki tavsif yozmang."
    )

    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    print(response.text)
    return response.text.strip()
