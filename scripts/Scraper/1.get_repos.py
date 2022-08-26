import requests
import time
import os.path
import json
import jsonpickle


queries = ["gibt+zurück", "gibt", "bestimmt+Objekt", "bestimmt", "gibt+bestimmt",
           "Klasse+bestimmt", "gibt+Klasse", "gibt+Objekt",
           "bestimmt+Objekt", "sucht", "sucht+Objekt", "sucht+Klasse", "sucht+bestimmt+gibt",
           "sucht+bestimmt+Objekt"]
repo_id = "https://api.github.com/repositories/490372641"
headers = {
    'User-Agent': 'Github Scraper',
    'Authorization': 'Token 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'
}

id_set = jsonpickle.decode(json.load((open("repo_name_list.json")))) if os.path.isfile("repo_name_list.json") else set()

for query in queries:
    for page_index in range(100):
        print(f"Scraping page {page_index}...")
        url = f"https://api.github.com/search/code?q={query}+in:file +language:java&per_page=100&page={page_index}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            for repository in response.json()["items"]:
                id_set.add(repository["repository"]["full_name"])
            time.sleep(90)
        else:
            print(response.status_code)
            break

json_set = jsonpickle.encode(id_set)
with open("repo_name_list.json", "w") as f:
    json.dump(json_set, f)

