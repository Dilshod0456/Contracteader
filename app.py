import os
import camelot
import json
from flask import Flask, request, jsonify, render_template
from find_cost import get_sort_csv, get_product_price
from dotenv import load_dotenv
import uuid


ilova = Flask(__name__)
ilova.config['YUKLASH'] = 'Uploads'
os.makedirs(ilova.config['YUKLASH'], exist_ok=True)
load_dotenv()

# pdf dan o'qitilgan ma'lumotlarni tozalash uchun
def toza_matn(matn):
    matn = matn.replace('```python', '')
    matn = matn.replace('```json', '')
    matn = matn.replace('```', '')
    return matn.strip()
# mahsulot narxlarini internetdan aniqlashtirish
def narx_tekshir(mah_narx, net_narx, chegara=0.25):
    try:
        mah_narx=float(str(mah_narx).replace(' ','').replace(',','').replace('UZS',''))
        net_narx = float(str(net_narx).replace(' ', '').replace(',', '').replace('UZS', ''))
        farq = abs(mah_narx - net_narx) / mah_narx
        return "Shubhali" if farq > chegara else "Ajoyib"
    except Exception:
        return "Xatolik"
    
# asosiy vazifani bajaruvchi api qism
@ilova.route('/api/yuklash', methods=['POST'])
def pdf_yuklash():
    if 'fayl' not in request.files:
        return jsonify({"xato": "Fayl topilmadi"}), 400
    fayl = request.files['fayl']
    if fayl.filename == '':
        return jsonify({"xato": "Fayl tanlanmadi"}), 400
    nom = f"{uuid.uuid4()}_{fayl.filename}"
    fayl_joy = os.path.join(ilova.config['YUKLASH'], nom)
    fayl.save(fayl_joy)
    try:
        jadvallar=camelot.read_pdf(fayl_joy,pages='all', flavor='stream')
        if len(jadvallar)==0:
            return jsonify({"xato": "PDF ichida jadval topilmadi"}),400
        csv_joy=os.path.join(ilova.config['YUKLASH'], 'chiq_jadval.csv')
        jadvallar[0].to_csv(csv_joy)
        with open(csv_joy, 'r', encoding='utf-8') as f:
            csv_matn=f.read()
        tartib_csv = get_sort_csv(csv_matn)
        tartib_csv = toza_matn(tartib_csv)
        try:
            malumot = json.loads(tartib_csv)
        except json.JSONDecodeError as x:
            return jsonify({"xato": f"JSONDecodeError: {str(x)}"}), 400
        natija = []
        for mah_nom, mah_narx in malumot.items():
            net_info = get_product_price(mah_nom)
            net_narx = list(net_info.values())[0]
            holat = narx_tekshir(mah_narx, net_narx)
            natija.append({"mahsulot": mah_nom,"yet_narx": mah_narx,"net_narx": net_narx,"holat": holat})
        os.remove(fayl_joy)
        if os.path.exists(csv_joy):
            os.remove(csv_joy)
        return jsonify({"natija": natija}), 200
    except Exception as x:
        if os.path.exists(fayl_joy):
            os.remove(fayl_joy)
        if os.path.exists(csv_joy):
            os.remove(csv_joy)
        return jsonify({"xato": f"Xatolik yuz berdi: {str(x)}"}), 500

# asosiy sahifa
@ilova.route('/')
def index():
    return render_template('index.html')
if __name__ == '__main__':
    ilova.run(debug=True)