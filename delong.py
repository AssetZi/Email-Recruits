# scrape_recruits.py
from __future__ import annotations

import csv
import os
import ssl
import smtplib
from typing import List, Tuple

from email.message import EmailMessage

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from messengerBot import send_telegram

# ----------------------------
# Config
# ----------------------------
CSV_PATH = "recruitData.csv"          # link,name,matchCount
TIMEOUT_SECONDS = 6                  # page/table wait
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT_SSL = 465

# Fill these (or set via environment variables)
EMAIL_SENDER = 'brockzacherl@gmail.com'
EMAIL_PASSWORD = 'bmfl ivmq iwne jixy'
EMAIL_RECEIVER = 'bmzacherl@pennwest.edu'

# ----------------------------
# Helpers
# ----------------------------
def sendDelong():
    scrapeRecruits('dcommitted.csv',True, 'Committs','delong_e@pennwest.edu')
    scrapeRecruits('duncommitted.csv',False, 'uncommitted','delong_e@pennwest.edu')
def load_csv(path: str) -> List[Tuple[str, str, int]]:
    rows: List[Tuple[str, str, int]] = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            link = row[0].strip()
            name = row[1].strip() if len(row) > 1 else ""
            try:
                count = int(row[2]) if len(row) > 2 else 1
            except ValueError:
                count = 1
            rows.append((link, name, count))
    return rows

def save_csv(path: str, rows: List[Tuple[str, str, int]]) -> None:
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    os.replace(tmp_path, path)  # atomic swap

def send_email(subject: str, body: str,recEmail: str) -> None:
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECEIVER:
        print("Email NOT sent (missing EMAIL_* config).")
        return
    em = EmailMessage()
    em["From"] = EMAIL_SENDER
    em["To"] = recEmail
    em["Subject"] = subject
    em.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT_SSL, context=context) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(em)

def scrape_profile(driver: webdriver.Safari, profile_url: str, already_count: int,isCommitted: bool) -> Tuple[List[str], int]:
    """
    Returns (new_lines, new_match_count)
    - new_lines: list of strings describing new matches
    - new_match_count: the updated total seen match count
    """
    div_num = 2
    driver.get(profile_url)
    if isCommitted:
        div_num = 3

    # Wait for any tbody under the main table
    try:
        WebDriverWait(driver, TIMEOUT_SECONDS).until(
            EC.presence_of_all_elements_located((By.XPATH, f'//*[@id="content"]/div[{div_num}]/table/tbody'))
        )
    except TimeoutException:
        # Page didn’t render expected table
        return [], already_count
        send_telegram('Error with Scrape')

    # Collect all rows once (across all tbodies)
    tbodies = driver.find_elements(By.XPATH, f'//*[@id="content"]/div[{div_num}]/table/tbody')

    rows = []
    for tbody in tbodies:
        rows.extend(tbody.find_elements(By.TAG_NAME, "tr"))
    total_rows = len(rows)
    if total_rows < 1 or already_count > total_rows:
        # Nothing new (or the stored count exceeded what’s on page)
        return [], max(already_count, total_rows)

    # Match counts are 1-indexed in your original code.
    # We want rows from index (already_count-1) to end.
    start_idx = max(already_count - 1, 0)
    new_rows = rows[start_idx:]

    new_lines: List[str] = []
    new_count = already_count

    for tr in new_rows:
        tds = tr.find_elements(By.TAG_NAME, "td")
        # Guard against layout changes
        date    = tds[0].text if len(tds) > 0 else "N/A"
        weight  = tds[1].text if len(tds) > 1 else "N/A"
        opp     = tds[2].text if len(tds) > 2 else "N/A"
        result  = tds[3].text if len(tds) > 3 else "N/A"
        new_lines.append(f"*{date} - {weight} - {opp}: {result}")
        new_count += 1

    return new_lines, new_count

# ----------------------------

def scrapeRecruits(csvPath: str,isCommitted:bool,title,receverEmail: str) -> None:
    # Load CSV
    recruits = load_csv(csvPath)  # [(link, name, matchCount), ...]

    # Start one browser for all work
    # driver = webdriver.Safari()
    options = Options()
    options.add_argument("--headless")        # optional
    options.add_argument("--no-sandbox")      # good for cron/mac mini
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)           # no service= needed
    email_chunks: List[str] = []
    updated_rows: List[Tuple[str, str, int]] = []

    try:
        for link, name, match_count in recruits:
            print(f"\nStarting: {name} ({match_count=})")

            new_lines, new_count = scrape_profile(driver, link, match_count,isCommitted)

            if new_lines:
                # Only emit a section if we found new results
                section = [f"{name}:"]
                section.extend(new_lines)
                email_chunks.append("\n".join(section))
                print(f"  + {len(new_lines)} new rows")

            # Keep rows aligned with (link, name, count)
            updated_rows.append((link, name, new_count))
    finally:
        driver.quit()

    # Persist updated counts
    save_csv(csvPath, updated_rows)

    # Email summary (only if anything changed)
    if email_chunks:
        body = "\n\n\n".join(email_chunks)
        send_email(subject=f"Daily Recruit Update {title}", body=body,recEmail=receverEmail)
        print("Email sent.")
    else:
        print("No new results; no email sent.")

    print("DONE!")
