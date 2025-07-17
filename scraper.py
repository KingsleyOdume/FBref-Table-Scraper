import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from playwright.sync_api import sync_playwright


def fetch_html_with_playwright(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"[INFO] Fetching with Playwright: {url}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"[ERROR] Playwright failed to fetch {url}: {e}")
            browser.close()
            raise e
        html = page.content()
        browser.close()
        return html
# Browser-like headers to reduce chance of being blocked
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://fbref.com/",
    "Connection": "keep-alive",
    "DNT": "1",
}


def scrape_premier_league():
    years = list(range(2022, 2020, -1))
    all_matches = []

    standings_url = "https://fbref.com/en/comps/9/Premier-League-Stats"

    for year in years:
        print(f"[INFO] Scraping season: {year}")
        try:
            html = fetch_html_with_playwright(standings_url)
        except Exception as e:
            print(f"[ERROR] Playwright failed to fetch {standings_url}: {e}")
            return False

        soup = BeautifulSoup(html, "html.parser")

        tables = soup.select('table.stats_table')
        if not tables:
            print(f"[ERROR] No table with class 'stats_table' found at {standings_url}")
            return False

        standings_table = tables[0]
        links = [l.get("href") for l in standings_table.find_all('a')]
        links = [l for l in links if '/squads/' in l]
        team_urls = [f"https://fbref.com{l}" for l in links]
        
        prev_links = soup.select("a.prev")
        if not prev_links:
            print(f"[ERROR] Could not find previous season link on {standings_url}")
            return False
        previous_season = prev_links[0].get("href")
        standings_url = f"https://fbref.com{previous_season}"

        for team_url in team_urls:
            team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
            print(f"[INFO] Scraping team: {team_name} ({year})")
            try:
                html = fetch_html_with_playwright(team_url)
            except Exception as e:
                print(f"[WARNING] Playwright failed to fetch {team_url}: {e}, skipping...")
                continue

            try:
                matches = pd.read_html(html, match="Scores & Fixtures")[0]
            except ValueError:
                print(f"[WARNING] No match table found for {team_name}, skipping...")
                continue

            soup = BeautifulSoup(html, "html.parser")
            links = [l.get("href") for l in soup.find_all('a')]
            links = [l for l in links if l and 'all_comps/shooting/' in l]
            if not links:
                print(f"[WARNING] No shooting stats link found for {team_name}, skipping...")
                continue

            shooting_url = f"https://fbref.com{links[0]}"
            try:
                html = fetch_html_with_playwright(shooting_url)
            except Exception as e:
                print(f"[WARNING] Playwright failed to fetch {shooting_url}: {e}, skipping...")
                continue

            try:
                shooting = pd.read_html(html, match="Shooting")[0]
                shooting.columns = shooting.columns.droplevel()
            except Exception as e:
                print(f"[WARNING] Failed to parse shooting stats for {team_name}: {e}, skipping...")
                continue


            try:
                team_data = matches.merge(
                    shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]],
                    on="Date"
                )
            except ValueError:
                print(f"[WARNING] Could not merge matches and shooting for {team_name}, skipping...")
                continue

            team_data = team_data[team_data["Comp"] == "Premier League"]
            team_data["Season"] = year
            team_data["Team"] = team_name
            all_matches.append(team_data)

            time.sleep(1)  # polite delay to avoid hammering FBref servers

    if all_matches:
        match_df = pd.concat(all_matches)
        match_df.columns = [c.lower() for c in match_df.columns]
        match_df.to_csv("matches.csv", index=False)
        print("[SUCCESS] Scraping completed. Data saved to matches.csv")
        return True
    else:
        print("[ERROR] No data scraped. matches.csv not created.")
        return False
