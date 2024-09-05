# coding=utf-8
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.request import urlretrieve
from selenium.webdriver.firefox.options import Options
import requests

DOMAIN = "nhentai.net"
# paste the cookie value here
COOKIE = "cookie here from request"

# Parse cookies
COOKIES = {}
for cookie in COOKIE.split(';'):
    key, value = cookie.strip().split('=', 1)
    COOKIES[key] = value

# Create an instance of Firefox options
firefox_options = Options()

# Disable DNS-over-HTTPS (DoH) in Firefox
firefox_options.set_preference("network.trr.mode", 5)
firefox_options.add_argument("--headless")

# download another geckodriver for your platform and replace it here
service = webdriver.FirefoxService(executable_path="bin/linux/geckodriver")
driver = webdriver.Firefox(service=service, options=firefox_options)

def parse_and_set_cookies(browser, cookie_string, domain):
    for cookie in cookie_string.split(';'):
        key, value = cookie.split('=', 1)
        cookie_dict = {
            'name': key.strip(),
            'value': value.strip(),
            'domain': domain,
            'path': '/'
        }
        browser.add_cookie(cookie_dict)

driver.get("https://nhentai.net/login/")
parse_and_set_cookies(driver, COOKIE, DOMAIN)
driver.get("https://nhentai.net/favorites/")

links = []

import time

nextelem = True
max_retries = 3  # Maximum number of retries
retry_delay = 5  # Delay in seconds between retries

while nextelem:
    curr = len(links)
    retries = 0

    while retries < max_retries:
        try:
            elem = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "cover"))  # This is a dummy element
            )
            elements = driver.find_elements(By.CLASS_NAME, "cover")

            for element in elements:
                link = element.get_attribute('href')
                if link:  # Ensure link is not None
                    links.append(link + "download")

            if len(driver.find_elements(By.CLASS_NAME, "next")) >= 1:
                driver.find_element(By.CLASS_NAME, "next").click()
                print(f"Fetching next page, current page had {str(abs(curr - len(links)))} # of elements, current total: {str(len(links))}")
            else:
                nextelem = False
                print(f"Reached the end, total links {len(links)}")

            break  # Exit retry loop if successful
        except Exception as e:
            retries += 1
            print(f"An error occurred: {str(e)}. Retrying {retries}/{max_retries}...")
            if retries < max_retries:
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Skipping to the next page.")
                driver.find_element(By.CLASS_NAME, "next").click()
                break

print("done fetching")
driver.quit()

print("starting dowload of .torrent files")
session = requests.Session()

for url in links:
    retry = True
    filename = url.split('/')[-2]
    filepath = "./dl/" + filename + ".torrent"

    if os.path.exists(filepath):
        print(f"File {filepath} already exists. Skipping download.")
        continue  # Skip this file and move to the next URL

    while retry:
        try:
            print("downloading " + url)
            response = session.get(url, cookies=COOKIES)

            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                retry = False  # Successful download, no need to retry

            elif response.status_code == 429:
                print(f"HTTP 429: Too many requests. Retrying in 5 seconds...")
                time.sleep(5)  # Wait for 5 seconds before retrying

            else:
                print(f"Failed to download {url}: {response.status_code}")
                retry = False  # Stop retrying on other errors

        except Exception as e:
            print(f"An error occurred while downloading {url}: {str(e)}")
            retry = False  # Stop retrying on exceptions
