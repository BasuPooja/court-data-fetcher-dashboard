# app/scraper.py
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def make_driver(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1400,1000")
    opts.add_argument("user-agent=CourtFetcherBot/1.0 (+https://yourdomain.example)")

    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    return driver


def fetch_case_data(case_type, case_number, filing_year, court_complex=None, headless=True, timeout=30):
    """
    Scrape court site and return flat dictionary with:
    registration_number, registration_date, judgment_date,
    petitioner, respondent, advocate_name, next_hearing_date,
    remark, state, district, status, raw_html, latest_pdf_link
    """

    # TODO: replace with the real court search URL
    base_search_url = "https://example-court-site.example/search"

    driver = None
    try:
        driver = make_driver(headless=headless)
        driver.get(base_search_url)

        wait = WebDriverWait(driver, timeout)

        # ==== Fill the form ====
        try:
            # case number
            case_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='case_number']"))
            )
            case_input.clear()
            case_input.send_keys(case_number)

            # filing year
            yr_input = driver.find_element(By.CSS_SELECTOR, "input[name='year']")
            yr_input.clear()
            yr_input.send_keys(filing_year)

            # case type
            try:
                driver.find_element(By.CSS_SELECTOR, "select[name='case_type']").send_keys(case_type)
            except NoSuchElementException:
                pass

            # submit
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            submit_btn.click()

        except TimeoutException:
            raise Exception("Search form not found on the court site.")

        time.sleep(1.5)  # allow JS to render results
        html = driver.page_source

        # ==== CAPTCHA / Block detection ====
        lower_html = html.lower()
        if "captcha" in lower_html or "recaptcha" in lower_html:
            raise Exception("CAPTCHA detected — cannot auto-scrape without solving it.")

        # ==== Extract Data ====
        def safe_text(selector, default=""):
            try:
                return driver.find_element(By.CSS_SELECTOR, selector).text.strip()
            except NoSuchElementException:
                return default

        registration_number = safe_text(".registration-number")
        registration_date = safe_text(".registration-date")
        judgment_date = safe_text(".judgment-date")
        petitioner = safe_text(".petitioner")
        respondent = safe_text(".respondent")
        advocate_name = safe_text(".advocate-name")
        next_hearing_date = safe_text(".next-hearing-date")
        remark = safe_text(".remark")
        state = safe_text(".state-name")
        district = safe_text(".district-name")
        status = safe_text(".case-status")

        # latest PDF link
        latest_pdf_link = ""
        try:
            pdf_links = driver.find_elements(By.CSS_SELECTOR, "a[href$='.pdf']")
            if pdf_links:
                latest_pdf_link = pdf_links[0].get_attribute("href")
        except Exception:
            pass

        return {
            "registration_number": registration_number,
            "registration_date": registration_date,
            "judgment_date": judgment_date,
            "petitioner": petitioner,
            "respondent": respondent,
            "advocate_name": advocate_name,
            "next_hearing_date": next_hearing_date,
            "remark": remark,
            "state": state,
            "district": district,
            "status": status,
            "raw_html": html,
            "latest_pdf_link": latest_pdf_link
        }

    except WebDriverException as e:
        raise Exception(f"WebDriver error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
