import cv2
import numpy as np
import itertools
import pytesseract
import os

def ocr_kiril_va_lotin(image):
    """
    Berilgan rasm faylidan rus+eng matnni qaytaradi.
    — project_root/tessdata ichida eng.traineddata va rus.traineddata bor
    """
    # 1) Tesseract executable joyi
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # 2) tessdata papkasining to‘liq yo‘li
    project_root = os.getcwd()
    tessdata_dir = os.path.join(project_root, 'tessdata')
    if not os.path.isdir(tessdata_dir):
        raise FileNotFoundError(f"tessdata papkasi topilmadi: {tessdata_dir}")
    
    # 3) TESSDATA_PREFIX muhit o‘zgaruvchisini tessdata papkasiga sozlaymiz
    os.environ['TESSDATA_PREFIX'] = tessdata_dir

    # 4) Rasmni yuklash va grayscale ga o‘tkazish
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 5) OCR chaqiruvi — rus+eng tillari birgalikda
    #    Hech qanday --tessdata-dir keraksiz: TESSDATA_PREFIX yetarli
    text = pytesseract.image_to_string(
        gray,
        lang='rus+eng',
        config='--psm 6'
    )
    return text.strip().replace('\n', " ")
 
def find_peak_lines(gray, density_frac=0.6):
    mask = make_hv_mask(gray)

    h, w = mask.shape
    # 1) Row & Col density
    row_density = mask.sum(axis=1)
    col_density = mask.sum(axis=0)

    # 2) Threshold values
    r_thresh = row_density.max() * density_frac
    c_thresh = col_density.max() * density_frac

    # 3) Rows above threshold
    rows_over = np.where(row_density >= r_thresh)[0]
    horiz_lines = []
    # group contiguous row indices
    for _, group in itertools.groupby(enumerate(rows_over), key=lambda iv: iv[0] - iv[1]):
        seg = [r for _, r in group]
        # choose central y
        y_mid = seg[len(seg)//2]
        # full‐width horizontal line
        horiz_lines.append((0, y_mid, w-1, y_mid))

    # 4) Cols above threshold
    cols_over = np.where(col_density >= c_thresh)[0]
    vert_lines = []
    for _, group in itertools.groupby(enumerate(cols_over), key=lambda iv: iv[0] - iv[1]):
        seg = [c for _, c in group]
        # choose central x
        x_mid = seg[len(seg)//2]
        # full‐height vertical line
        vert_lines.append((x_mid, 0, x_mid, h-1))

    return horiz_lines, vert_lines


# — Misol foydalanish —
# 1) edges → Hough → mask yasaymiz:

def make_hv_mask(gray,
                 canny_t1=30, canny_t2=150,
                 hough_thresh=50, min_len=100, max_gap=20,
                 angle_tol=5, thickness=2):
    edges = cv2.Canny(gray, canny_t1, canny_t2)
    raw = cv2.HoughLinesP(edges, 1, np.pi/180, hough_thresh,
                          minLineLength=min_len, maxLineGap=max_gap)
    mask = np.zeros_like(edges)
    if raw is not None:
        for x1,y1,x2,y2 in raw[:,0]:
            ang = abs(np.degrees(np.arctan2(y2-y1, x2-x1)))
            if ang < angle_tol or abs(ang-90) < angle_tol:
                cv2.line(mask, (x1,y1), (x2,y2), 255, thickness)
    return mask


def cut_cells(gray, horiz_lines, vert_lines):
    # Sort lines by position
    h_lines = sorted(list(set([y1 for _, y1, _, _ in horiz_lines])))
    v_lines = sorted(list(set([x1 for x1, _, _, _ in vert_lines])))
    
    # Initialize cells list
    cells = []
    
    # Extract each cell
    for i in range(len(h_lines) - 1):
        row_cells = []
        for j in range(len(v_lines) - 1):
            # Get cell coordinates
            y1, y2 = h_lines[i], h_lines[i+1]
            x1, x2 = v_lines[j], v_lines[j+1]
            
            # Extract cell image
            cell = gray[y1:y2, x1:x2]
            row_cells.append(cell)
            
        cells.append(row_cells)
    
    return cells



def to_table(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    horiz_lines, vert_lines = find_peak_lines(gray, density_frac=0.6)
    cells = cut_cells(gray, horiz_lines, vert_lines)
    for i, row in enumerate(cells):
        for j, col in enumerate(row):
            img = cv2.cvtColor(cells[i][j], cv2.COLOR_BGR2RGB)
            text = ocr_kiril_va_lotin(img)
            cells[i][j] = text
    return cells