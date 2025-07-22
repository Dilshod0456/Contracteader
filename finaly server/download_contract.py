from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_detail_page_urls(list_url, driver=None, headless=True, timeout=15):
    own_driver = False
    if driver is None:
        chrome_opts = webdriver.ChromeOptions()
        if headless:
            chrome_opts.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_opts)
        own_driver = True

    try:
        driver.get(list_url)
        wait = WebDriverWait(driver, timeout)
        # wait for items to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".lot-list .lot-item")))

        items = driver.find_elements(By.CSS_SELECTOR, ".lot-list .lot-item")[:10]
        detail_urls = []
        original_window = driver.current_window_handle

        for item in items:
            btn = item.find_element(By.CSS_SELECTOR, "a.btn.btn-lg.btn-primary")
            before_windows = set(driver.window_handles)
            btn.click()

            # wait for either new window or URL change
            wait.until(lambda d: len(d.window_handles) != len(before_windows)
                                 or d.current_url != list_url)

            new_windows = set(driver.window_handles) - before_windows
            if new_windows:
                # new tab/window opened
                handle = new_windows.pop()
                driver.switch_to.window(handle)
                wait.until(lambda d: d.current_url and d.current_url != "about:blank")
                detail_urls.append(driver.current_url)
                driver.close()
                driver.switch_to.window(original_window)
            else:
                # navigation happened in the same tab
                wait.until(EC.url_changes(list_url))
                detail_urls.append(driver.current_url)
                driver.back()
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".lot-list .lot-item")))
                original_window = driver.current_window_handle

        return detail_urls

    finally:
        if own_driver:
            driver.quit()

def download_contract_pdf(detail_url, save_folder="Contracts/xariduz", headless=True, timeout=30):
    """
    Navigate to `detail_url`, click the "Faylni yuklab olish" button,
    wait for the new PDF to download, then rename it uniquely
    (timestamp + UUID) in `save_folder`.

    Returns:
      Path to the uniquely named PDF file.
    """
    save_path = Path(save_folder)
    save_path.mkdir(parents=True, exist_ok=True)

    chrome_opts = webdriver.ChromeOptions()
    if headless:
        chrome_opts.add_argument("--headless=new")
    prefs = {
        "download.default_directory": str(save_path.resolve()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_opts.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_opts)

    try:
        driver.get(detail_url)
        wait = WebDriverWait(driver, 15)
        btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[contains(text(), 'Faylni yuklab olish')]"
        )))

        # Record files before download
        before_files = set(save_path.glob("*.pdf"))

        btn.click()

        # Wait for a new PDF to appear
        end_time = time.time() + timeout
        new_file = None
        while time.time() < end_time:
            after_files = set(save_path.glob("*.pdf"))
            diff = after_files - before_files
            if diff:
                new_file = diff.pop()
                break
            time.sleep(0.5)

        if not new_file:
            raise RuntimeError(f"No new PDF appeared within {timeout}s")

        # Build unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex
        new_name = f"contract_{timestamp}_{unique_id}.pdf"
        dest = save_path / new_name

        new_file.rename(dest)
        return dest

    finally:
        driver.quit()

urls = get_detail_page_urls("https://xarid.uzex.uz/purchase/e-direct-purchase/list")

for url in urls:
    try:
        print(f"Processing URL: {url}")
        pdf_path = download_contract_pdf(url)
        print(f"Downloaded PDF to: {pdf_path}")
    except Exception as e:
        print(f"Failed to download PDF from {url}: {e}")

