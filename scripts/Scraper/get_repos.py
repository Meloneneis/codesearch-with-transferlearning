import requests
import time
import os.path
import json
import jsonpickle

repo_id = "https://api.github.com/repositories/490372641"
headers = {
    'User-Agent': 'Github Scraper',
    'Authorization': 'Token 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'
}

id_set = jsonpickle.decode(json.load((open("repo_list.json")))) if os.path.isfile("repo_list.json") else set()

for page_index in range(100):
    print(f"Scraping page {page_index}...")
    url = f"https://api.github.com/search/code?q=bestimmt+in:file +language:java&per_page=100&page={page_index}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        for repository in response.json()["items"]:
            id_set.add(repository["repository"]["id"])
        time.sleep(90)
    else:
        break

json_set = jsonpickle.encode(id_set)
with open("repo_list.json", "w") as f:
    json.dump(json_set, f)

