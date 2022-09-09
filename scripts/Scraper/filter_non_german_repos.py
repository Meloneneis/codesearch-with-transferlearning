import requests
import time
import json
import jsonpickle
from tqdm import tqdm
import base64
import urlfetch
from tree_sitter import Language, Parser
import jsonlines
from transformers import AutoModel
import langdetect

JAVA_LANGUAGE = Language('build/my-languages.so', 'java')
parser = Parser()
parser.set_language(JAVA_LANGUAGE)

method_query = JAVA_LANGUAGE.query("""
(
  (method_declaration) @method
)
""")
doc_query = JAVA_LANGUAGE.query("""
(
  (doc_comment) @doc
)
""")

headers = {
    'User-Agent': 'Github Scrapers',
    'Authorization': 'Token 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'
}
star_count = 5
name_set = jsonpickle.decode(json.load((open(f"repo_data/filtered_starcount_{star_count}_repo_list.json"))))
german_eval_data = []
german_repos = set()

for repo_name in tqdm(name_set, desc="Repos"):
    skipRepo = False
    german_test = 0
    noDocCounter = 0
    print(f"\n{repo_name}")

    repo_request = requests.get(f"https://api.github.com/repos/{repo_name}/git/trees/master?recursive=1", headers=headers)
    repo_json = repo_request.json() if repo_request.status_code == 200 else print(repo_request.status_code)
    if repo_request.status_code is not 200:
        skipRepo = True
        continue
    java_files = [file for file in repo_json["tree"] if file["path"].endswith(".java")]
    for file in java_files:
        if noDocCounter > 50:
            skipRepo = True
        if skipRepo:
            break
        time.sleep(0.1)
        try:
            result = urlfetch.fetch(file["url"], headers=headers)
            data = json.loads(result.content) if result.status_code == 200 else print(result.status_code)
            decoded_content = base64.b64decode(data["content"])
            tree = parser.parse(bytes(decoded_content))
            method_captures = method_query.captures(tree.root_node)
            for capture in method_captures:
                if skipRepo:
                    break
                if capture[0].prev_sibling.type == "doc_comment" or capture[0].next_sibling.type == "doc_comment":
                    docstring = capture[0].prev_sibling.text.decode("ISO-8859-1") if \
                        capture[0].prev_sibling.type == "doc_comment" else \
                        capture[0].next_sibling.text.decode("ISO-8859-1")
                    if langdetect.detect(docstring) != "de":
                        german_test -= 1
                        print(german_test, end=" ")
                        if german_test < -5:
                            print(f"{repo_name} not added")
                            skipRepo = True
                        break
                    german_test += 1
                    print(german_test, end=" ")
                    noDocCounter = 0
                    time.sleep(0.1)
                    if german_test > 5:
                        print(f"{repo_name} added")
                        german_repos.add(repo_name)
                        skipRepo = True
                        break
                else:
                    noDocCounter += 1
                    if noDocCounter == 50:
                        print("no docs found.. skip repo..")
                    continue
        except:
            pass


json_set = jsonpickle.encode(german_repos)
with open("repo_data/german_repos.json", "w") as f:
    json.dump(json_set, f)
