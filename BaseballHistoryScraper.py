import os
import traceback
from io import StringIO
from time import sleep

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class BaseballHistoryScraper:
    BASE_URL = "https://www.baseball-almanac.com"
    START_URL = f"{BASE_URL}/yearmenu.shtml"

    def __init__(self, headless=True):
        self.driver = self._setup_driver(headless)

    @staticmethod
    def _setup_driver(headless):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920x1080')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/113.0')
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(20)

        return driver

    def scrape(self):
        try:
            print(f"[INFO] Accessing main page: {self.START_URL}")
            self.driver.get(self.START_URL)

            # Getting a list of links for all years
            year_links = self._get_year_links()
            if not year_links:
                raise ValueError(
                    "[ERROR] No `Baseball History in 1901 in the American League` title founds. Double check site structure or selectors.")
            print(f"[INFO] American League: Found {len(year_links)} years")

            year_count = 0
            for year, link in sorted(year_links.items()):
                year_count += 1
                retries = 2

                # I got lots of timeouts, so adjust logic with retries
                for attempt in range(retries):
                    try:
                        print(f"[INFO] Scraping year {year} at {link} (Attempt {attempt + 1}/{retries})")
                        self.driver.get(link)
                        self._parse_and_save_year_data(year)

                        # 4 seconds were a result of dozens of failed tries
                        sleep(4)

                        break
                    except TimeoutException as e:
                        print(f"[TIMEOUT] Year {year} took too long on attempt {attempt + 1}. Retrying...")
                        self._log_exception(e)

                        if attempt + 1 == retries:
                            print(f"[ERROR] Giving up on year {year} after {retries} attempts.")
                    except Exception as e:
                        print(f"[ERROR] Unexpected error scraping year {year}. Skipping...")
                        self._log_exception(e)

                        break

                # I got lots of timeouts, so adjust logic with restarting Chrome driver
                if year_count % 10 == 0:
                    print("[INFO] Restarting driver to avoid stale session.")
                    self.driver.quit()
                    self.driver = self._setup_driver(headless=True)

        except Exception as e:
            self._log_exception(e)
        finally:
            self.driver.quit()

    def _get_year_links(self):
        year_links = {}
        try:
            # I decided to work only with American League for now
            link_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 'td.datacolBox a[title*="in the American League"]'
            )
            print(f"[DEBUG] Found {len(link_elements)} AL year links")

            for elem in link_elements:
                year_text = elem.text.strip()
                year_href = elem.get_attribute("href")
                if year_text.isdigit() and year_href:
                    full_link = (
                        year_href if year_href.startswith("http")
                        else f"{self.BASE_URL}/{year_href.lstrip('/')}"
                    )
                    year_links[year_text] = full_link

        except Exception as e:
            print("[ERROR] Failed to extract American League year links.")
            self._log_exception(e)

        return year_links

    def _parse_and_save_year_data(self, year):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
            )

            tables = self.driver.find_elements(By.CSS_SELECTOR, "table")
            print(f"[INFO] Found {len(tables)} tables for year {year}")

            os.makedirs("scraped_data", exist_ok=True)
            for idx, table in enumerate(tables, start=1):
                table_title = self._extract_table_title(table, year)

                df = self._parse_html_table(table)
                if df is not None and not df.empty:
                    # Here is a list of dirty hacks I added to simplify data cleanup in the future
                    # They are mostly making columns more consistent as Baseball League site shows so versatile data through years
                    if int(year) <= 1968 and table_title in ["American League", "American League Standings",
                                                             "American League Team Standings"]:
                        df.insert(0, "Conference", "Conference placeholder")
                    if int(year) <= 1980 and table_title in ["American League Team Standings"]:
                        df.insert(3, "Strike Splits", "Strike Splits placeholder")
                    if int(year) <= 1984 and table_title in ["American League", "American League Standings",
                                                             "American League Team Standings"]:
                        df.insert(len(df.columns), "Payroll", "Payroll placeholder")
                    if int(year) <= 2002 and int(year) != 1928 and table_title in ["American League",
                                                                                   "American League Standings",
                                                                                   "American League Team Standings"]:
                        df.insert(4, "Ties", "Ties placeholder")
                    df.insert(0, "Year", year)

                    safe_title = table_title.replace(" ", "_").replace("/", "_").replace("|", "_")[:50]
                    csv_filename = f"scraped_data/{safe_title}.csv"
                    df.to_csv(csv_filename, mode="a", header=False, index=False)
                    print(f"[INFO] Saved {csv_filename}")

        except Exception as e:
            print(f"[ERROR] Failed to extract data for year {year}.")
            self._log_exception(e)

    def _parse_html_table(self, table_element):
        try:
            html = table_element.get_attribute('outerHTML')
            # I use pandas read_html as a quick option to not do an additional parsing
            dfs = pd.read_html(StringIO(html))
            if dfs:
                return dfs[0]
        except Exception as e:
            print("[ERROR] Failed to parse table.")
            self._log_exception(e)

        return None

    def _extract_table_title(self, table_element, year=None):
        try:
            h2 = table_element.find_elements(By.CSS_SELECTOR, "h2")
            if h2:
                raw_title = h2[0].text.strip()
                return self._clean_title(raw_title, year)

            # Added fall back to first cell with class header or banner if there are no h2 tag
            header_cells = table_element.find_elements(By.CSS_SELECTOR, "td.header, td.banner")
            if header_cells:
                raw_title = header_cells[0].text.strip()
                return self._clean_title(raw_title, year)

        except Exception:
            pass

        return "UnknownTable"

    @staticmethod
    def _clean_title(title, year):
        # I remove year prefix from the title if it matches the given year to make titles consistent
        if year and title.startswith(str(year)):
            return title[len(str(year)):].strip(" .-")

        return title

    @staticmethod
    def _clean_dataframe(df):
        df.columns = [col.strip() for col in df.columns]
        df.dropna(how="all", inplace=True)

        return df

    @staticmethod
    def _log_exception(e):
        trace_back = traceback.extract_tb(e.__traceback__)
        stack_trace = [f'File: {trace[0]}, Line: {trace[1]}, Func: {trace[2]}, Message: {trace[3]}' for trace in
                       trace_back]
        print(f"[EXCEPTION] {type(e).__name__}: {e}")
        print(f"[STACK TRACE] {stack_trace}")


if __name__ == "__main__":
    scraper = BaseballHistoryScraper(headless=True)
    scraper.scrape()
