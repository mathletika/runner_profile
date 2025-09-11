# get_pb.py
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

# Automatikus ChromeDriver letöltés/telepítés
chromedriver_autoinstaller.install()

def scrape_world_athletics_pbs(url: str, wait_sec: int = 45):
    """
    Bemenet: WA profil URL
    Kimenet: list[dict] a kulcsokkal: Discipline, Performance, Date (YYYY-MM-DD vagy None), Score (vagy None)
    Csak a Statistics -> Personal Bests fülről olvas.
    """
    if not isinstance(url, str) or not url.strip():
        return []

    # ---- Chrome headless beállítások
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1366,900")
    options.add_argument("--lang=en-US")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)

    try:
        # ---- Oldal betöltés
        driver.get(url)
        WebDriverWait(driver, wait_sec).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # ---- STATISTICS fül
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@value='STATISTICS']"))
        ).click()

        # ---- Personal bests tab
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@value='Personal bests']"))
        ).click()

        # ---- Táblázat megvárása
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        tables = driver.find_elements(By.TAG_NAME, "table")
        rows_out = []

        for tbl in tables:
            rows = tbl.find_elements(By.TAG_NAME, "tr")
            if not rows or len(rows) < 2:
                continue

            headers = [th.text.strip() for th in rows[0].find_elements(By.TAG_NAME, "th")]
            body_rows = rows[1:]

            for r in body_rows:
                tds = r.find_elements(By.TAG_NAME, "td")
                if len(tds) < 2:
                    continue
                disc = tds[0].text.strip()
                perf = tds[1].text.strip()
                date = None
                score = None

                # dátum keresés
                if len(tds) >= 4:
                    maybe_date = tds[3].text.strip()
                    date = maybe_date if any(ch.isdigit() for ch in maybe_date) else None
                elif len(tds) >= 3:
                    maybe_date = tds[2].text.strip()
                    date = maybe_date if any(ch.isdigit() for ch in maybe_date) else None

                # Score, ha van
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

            if rows_out:
                break

        if not rows_out:
            return []

        # ---- Tisztítás és normalizálás
        df = pd.DataFrame(rows_out)

        # biztos oszlopok
        for c in ["Discipline", "Performance", "Date", "Score"]:
            if c not in df.columns:
                df[c] = None

        # Eredmény formázás: vessző -> pont
        df["Performance"] = df["Performance"].astype(str).str.replace(",", ".", regex=False)

        # Dátum ISO
        def _to_iso(x):
            try:
                d = pd.to_datetime(x, errors="coerce")
                return d.date().isoformat() if pd.notna(d) else None
            except Exception:
                return None
        df["Date"] = df["Date"].apply(_to_iso)

        # Üres sorok kiszűrése
        df = df[~df["Discipline"].isna() & df["Performance"].astype(str).str.len().gt(0)]

        return df.to_dict(orient="records")

    finally:
        driver.quit()
