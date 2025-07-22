import os
import camelot
import json
from flask import Flask, render_template, request
from find_cost import get_sort_csv, get_product_price
from dotenv import load_dotenv
from pdf_to_table_img import extract_tables_from_pdf
from image_to_table import to_table
# Flask app yaratish
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
load_dotenv()

def clean_gpt_output(text):
    text = text.replace('```python', '')
    text = text.replace('```json', '')
    text = text.replace('```', '')
    return text.strip()

def check_price_anomaly(local_price, online_price, threshold=0.25):
    try:
        local_price = float(str(local_price).replace(' ', '').replace(',', '').replace('UZS', ''))
        online_price = float(str(online_price).replace(' ', '').replace(',', '').replace('UZS', ''))
        diff = abs(local_price - online_price) / local_price
        return "Shubhali" if diff > threshold else "Ajoyib"
    except Exception:
        return "Xatolik"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "Fayl topilmadi", 400

        file = request.files['file']
        if file.filename == '':
            return "Fayl tanlanmadi", 400

        # Faylni saqlash
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # PDF faylidan jadvalni rasm sifatida chiqarish
        tables_imgs = extract_tables_from_pdf(file_path)
        tables_list = []
        for table_img in tables_imgs:
            table_img = table_img['image']
            tables_list += to_table(table_img)

        json_data = []
        headers = tables_list[0]
        print(headers)
        for row in tables_list[1:]:
            item = {}
            for i, value in enumerate(row):
                key = headers[i] if 1 < len(headers[i]) else f'column_{i}'
                item[key] = value
            json_data.append(item)
        try:
            json_text = json.dumps(json_data, ensure_ascii=False, indent=4)
        except json.JSONDecodeError as e:
            return f"JSONDecodeError: {e}", 400
        print(json_text)
        results = []
        results.append(json_text)

        # for product_name, local_price in extracted_data.items():
        #     online_info = get_product_price(product_name)
        #     online_price = list(online_info.values())[0]  # Faqat qiymatini olish
        #     status = check_price_anomaly(local_price, online_price)

        #     results.append({
        #         "mahsulot": product_name,
        #         "yetkazib_berish_narxi": local_price,
        #         "internet_narxi": online_price,
        #         "status": status
        #     })

        return render_template('result.html', results=results)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
