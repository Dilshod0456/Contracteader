import os
import fitz  # PyMuPDF
import cv2
import numpy as np

def extract_tables_from_pdf(pdf_path):
    """
    PDFdan 7 ustunli jadvallarni aniqlab, ularni rasm ko'rinishida qaytaradi.
    Args:
        pdf_path (str): PDF faylning to'liq yo'li.
    Returns:
        list: Har bir element quyidagi kalitlarga ega bo'lgan lug'atdan iborat ro'yxat:
            - 'page' (int): Jadval aniqlangan sahifa raqami (1 dan boshlanadi).
            - 'table' (int): Sahifadagi jadval tartib raqami.
            - 'columns' (int): Jadvaldagi ustunlar soni (faqat 7 ustunli jadvallar).
            - 'image' (np.ndarray): Jadvalning rasm ko'rinishidagi numpy massiv ko'rinishi (BGR formatda).
    Raises:
        Exception: PDFni ochishda yoki rasmni qayta ishlashda xatolik yuz bersa, bo'sh ro'yxat qaytariladi.
    Qadamlar:
        1. PDF faylni ochadi va har bir sahifani ko'rib chiqadi.
        2. Sahifani rasmga aylantiradi va uni OpenCV yordamida o'qiydi.
        3. Rasmni kulrangga o'tkazadi va adaptiv threshold bilan binarizatsiya qiladi.
        4. Gorizontal va vertikal chiziqlarni morfologik operatsiyalar yordamida ajratib oladi.
        5. Jadval konturlarini topadi va har bir jadval uchun:
            - Jadval rasm qismini ajratadi.
            - Vertikal chiziqlar asosida ustunlar sonini aniqlaydi.
            - Faqat 7 ustunli jadvallarni ro'yxatga qo'shadi.
        6. Natijada, 7 ustunli jadvallar ro'yxatini qaytaradi.
    """
    """PDFdan 7 ustunli jadvallarni aniqlab ko'rsatadi"""
    try:
        doc = fitz.open(pdf_path)
        file_basename = os.path.basename(pdf_path).replace('.pdf', '')
        tables_found = 0
        seven_column_tables = []  # 7 ustunli jadvallar uchun list
        
        
        for page_num, page in enumerate(doc):
            
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            img_data = pix.tobytes("png")
            
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            img_orig = img.copy()
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY_INV, 11, 2)
            
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
            
            horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
            vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=1)
            
            table_mask = cv2.add(horizontal_lines, vertical_lines)
            
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            min_area = 10000
            table_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
            
            for i, contour in enumerate(table_contours):
                x, y, w, h = cv2.boundingRect(contour)
                padding = 10
                x = max(0, x - padding)
                y = max(0, y - padding)
                w = min(img_orig.shape[1] - x, w + 2*padding)
                h = min(img_orig.shape[0] - y, h + 2*padding)
                
                table_img = img_orig[y:y+h, x:x+w]
                table_gray = cv2.cvtColor(table_img, cv2.COLOR_BGR2GRAY)
                
                vertical_kernel_detailed = cv2.getStructuringElement(cv2.MORPH_RECT, (1, h//3))
                vertical_lines_detailed = cv2.morphologyEx(cv2.threshold(table_gray, 0, 255, 
                    cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1], cv2.MORPH_OPEN, vertical_kernel_detailed)
                
                v_projection = np.sum(vertical_lines_detailed, axis=0)
                
                threshold = np.max(v_projection) * 0.3
                column_edges = np.where(v_projection > threshold)[0]
                
                min_distance = 20
                column_boundaries = []
                if len(column_edges) > 0:
                    current_boundary = column_edges[0]
                    for edge in column_edges[1:]:
                        if edge - current_boundary > min_distance:
                            column_boundaries.append(current_boundary)
                            current_boundary = edge
                    column_boundaries.append(current_boundary)
                
                num_columns = len(column_boundaries) - 1 if len(column_boundaries) > 1 else 1
                
                # Faqat 7 ustunli jadvallarni saqlash
                if num_columns == 7:
                    seven_column_tables.append({
                        'page': page_num + 1,
                        'table': i + 1,
                        'columns': num_columns,
                        'image': table_img,
                    })
                
                
                tables_found += 1
        
        return seven_column_tables
    
    except Exception as e:
        return []
