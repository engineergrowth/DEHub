import requests
import re

print("Starting the script...")

with open("README.md", "r") as file:
    content = file.read()

urls = re.findall(r'https?://[^\s\)\]]+', content)

for url in urls:
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        if response.status_code != 200:
            print(f"Broken link: {url} (Status code: {response.status_code})")
        else:
            print(f"Valid link: {url}")
    except requests.RequestException as e:
        print(f"Error with link: {url} ({e})")

#TODO test broken links 