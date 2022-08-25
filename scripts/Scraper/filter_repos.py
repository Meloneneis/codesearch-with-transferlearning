import requests
import time
import json
import jsonpickle
from tqdm import tqdm

headers = {
    'User-Agent': 'Github Scraper',
    'Authorization': 'Token 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'
}

id_set = jsonpickle.decode(json.load((open("repo_list.json"))))
filtered_set = set()
for repo_id in tqdm(id_set, desc="Filterprogress"):
    url = f"https://api.github.com/repositories/{repo_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        if response.json()["stargazers_count"] > 5:
            filtered_set.add(repo_id)
    else:
        print(f"For id {repo_id} this error happened: {response.json()['message']}")

json_set = jsonpickle.encode(filtered_set)
print(f"Size of filtered repo list: {len(json_set)}")
with open("filtered_repo_list.json", "w") as f:
    json.dump(json_set, f)

