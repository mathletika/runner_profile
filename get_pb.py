# get_pb.py
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _make_driver():
    """Headless Chromium driver a Streamlit Cloudhoz (fix path-okkal, old headless móddal)."""
    options = Options()
    options.binary_location = "/usr/bin/chromium"  # Debian bullseye alatt
    options.add_argument("--headless=old")  # <<< stabilabb headless mód
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1366,900")
    options.add_argument("--lang=en-US")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    driver_path = "/usr/bin/chromedriver"
    return webdriver.Chrome(service=Service(driver_path), options=options)


def scrape_world_athletics_pbs(url: str, wait_sec: int = 45):
    """
    WA profil Personal Bests fül scraping.
    Visszatérés: list[dict] kulcsokkal: Discipline, Performance, Date, Score
    """
    if not isinstance(url, str) or not url.strip():
        return []

    driver = _make_driver()
    try:
        driver.get(url)
        WebDriverWait(driver, wait_sec).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Navigáció: STATISTICS fül (a vagy button)
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//a[contains(.,'Statistics')] | //button[contains(.,'Statistics')]"
            ))
        ).click()

        # Navigáció: Personal bests tab (a vagy button)
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//a[contains(.,'Personal Best')] | //button[contains(.,'Personal Best')]"
            ))
        ).click()

        # Várjuk a táblát
        try:
            table = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "(//h2[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'personal best')]/following::table)[1]"
                    " | //table[.//th[normalize-space()='Discipline'] and .//th[contains(.,'Performance')]]"
                ))
            )
        except Exception:
            # Debug HTML kinyomtatása a logba
            print("DEBUG: Az oldal első 2000 karaktere:\n")
            print(driver.page_source[:2000])
            raise

        rows_out = []
        rows = table.find_elements(By.XPATH, ".//tr")
        if len(rows) > 1:
            headers = [th.text.strip() for th in rows[0].find_elements(By.TAG_NAME, "th")]
            for r in rows[1:]:
                tds = r.find_elements(By.TAG_NAME, "td")
                if len(tds) < 2:
                    continue
                disc = tds[0].text.strip()
                perf = tds[1].text.strip()
                date = None
                score = None

                if len(tds) >= 4:
                    maybe_date = tds[3].text.strip()
                    date = maybe_date if any(ch.isdigit() for ch in maybe_date) else None
                elif len(tds) >= 3:
                    maybe_date = tds[2].text.strip()
                    date = maybe_date if any(ch.isdigit() for ch in maybe_date) else None

                headers_lower = [h.lower() for h in headers]
                if "score" in headers_lower:
                    try:
                        idx = headers_lower.index("score")
                        if idx < len(tds):
                            score = tds[idx].text.strip()
                    except Exception:
                        score = None

                if disc and perf:
                    rows_out.append({
                        "Discipline": disc,
                        "Performance": perf,
                        "Date": date,
                        "Score": score
                    })

        if not rows_out:
            return []

        # ---- Normalizálás Pandas-szal
        df = pd.DataFrame(rows_out)
        for c in ["Discipline", "Performance", "Date", "Score"]:
            if c not in df.columns:
                df[c] = None

        df["Performance"] = df["Performance"].astype(str).str.replace(",", ".", regex=False)

        def _to_iso(x):
            try:
                d = pd.to_datetime(x, errors="coerce")
                return d.date().isoformat() if pd.notna(d) else None
            except Exception:
                return None

        df["Date"] = df["Date"].apply(_to_iso)
        df = df[~df["Discipline"].isna() & df["Performance"].astype(str).str.len().gt(0)]

        return df.to_dict(orient="records")

    finally:
        driver.quit()
