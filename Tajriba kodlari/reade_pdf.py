import camelot
import json
from find_cost import get_sort_csv

def extract_clean_tables_from_pdf_with_camelot(pdf_path, output_prefix="jadval_clean.csv"):
    # 1. PDF'dan jadval o'qish
    tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')

    # 2. CSV'ga saqlash
    tables[0].to_csv(output_prefix)

    # 3. CSV matnini o'qish
    with open(output_prefix, 'r', encoding='utf-8') as f:
        csv_text = f.read()

    # 4. get_sort_csv() dan natija olish
    sorted_csv_text = get_sort_csv(csv_text)


    # 5. Tozalash (IMPORTANT!)
    sorted_csv_text = sorted_csv_text.replace('```python', '')
    sorted_csv_text = sorted_csv_text.replace('```', '')
    sorted_csv_text = sorted_csv_text.strip()

    # 6. JSON ga o‘girish
    if sorted_csv_text:
        try:
            result_dict = json.loads(sorted_csv_text)
            return result_dict
        except json.JSONDecodeError as e:
            return None
    else:
        return None

# ✅ Misol chaqiruv
file_path = "contracts/4.pdf"
result = extract_clean_tables_from_pdf_with_camelot(file_path)

print(result)
print(type(result))
