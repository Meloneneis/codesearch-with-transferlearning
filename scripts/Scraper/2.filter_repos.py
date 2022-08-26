import requests
import time
import json
import jsonpickle
from tqdm import tqdm

headers = {
    'User-Agent': 'Github Scraper',
    'Authorization': 'Token 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'
}
star_count = 9
id_set = jsonpickle.decode(json.load((open("repo_list.json"))))
print(len(id_set))
filtered_set = set()
for repo_id in tqdm(id_set, desc="Filterprogress"):
    url = f"https://api.github.com/repositories/{repo_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        if response.json()["stargazers_count"] > star_count:
            filtered_set.add(repo_id)
    else:
        print(f"For id {repo_id} this error happened: {response.json()['message']}")

json_set = jsonpickle.encode(filtered_set)
print(f"Size of filtered repo list: {len(json_set)}")
with open(f"filtered_starcount_{star_count+1}_repo_list.json", "w") as f:
    json.dump(json_set, f)

