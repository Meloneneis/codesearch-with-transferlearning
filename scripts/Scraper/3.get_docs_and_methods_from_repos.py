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

Language.build_library(
    # Store the library in the `build` directory
    'build/my-languages.so',

    # Include one or more languages
    [
        'tree-sitter-java'
    ]
)
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


def docstring_processor(docstring):
    return

'''
This code block will traverse over every repo in the set and filter the docstring with its respective code function.
Every repo starts with num_Chances of the documentation being german and after 5 consecutive cases of it not being the case, the repo will be skipped.
The chances will be reset to num_Chances on detecting german docstring.
'''
num_Chances = 7
for repo_name in tqdm(name_set, desc="Repos"):
    print(f"\n{repo_name}")
    isGerman = True
    chanceForGerman = num_Chances
    if not isGerman:
        break
    repo_request = requests.get(f"https://api.github.com/repos/{repo_name}/git/trees/master?recursive=1", headers=headers)
    repo_json = repo_request.json() if repo_request.status_code == 200 else print(repo_request.status_code)
    java_files = [file for file in repo_json["tree"] if file["path"].endswith(".java")]
    for file in tqdm(java_files, desc="Java files processed"):
        if not isGerman:
            break
        time.sleep(0.1)
        result = urlfetch.fetch(file["url"], headers=headers)
        data = json.loads(result.content) if result.status_code == 200 else print(result.status_code)
        decoded_content = base64.b64decode(data["content"])
        tree = parser.parse(bytes(decoded_content))
        method_captures = method_query.captures(tree.root_node)
        for capture in method_captures:
            try:
                if capture[0].prev_sibling.type == "doc_comment" or capture[0].next_sibling.type == "doc_comment":
                    docstring = capture[0].prev_sibling.text.decode("ISO-8859-1") if \
                        capture[0].prev_sibling.type == "doc_comment" else \
                        capture[0].next_sibling.text.decode("ISO-8859-1")
                    if langdetect.detect(docstring) != "de":
                        chanceForGerman -= 1
                        print(f"{docstring} is not German! {chanceForGerman} chances left, else skip this repo..")
                        if chanceForGerman < 1:
                            print("That was the last chance... skip this repo...")
                            isGerman = False
                        break
                    print(f"{docstring} is actually german :)")
                    chanceForGerman = num_Chances
                    method = capture[0].text.decode("ISO-8859-1")
                    # skip duplicates
                    if {"docstring": docstring, "function": method} in german_eval_data:
                        break
                    german_eval_data.append({"docstring": docstring, "function": method})
                    time.sleep(0.1)
                else:
                    continue
            except:
                pass


with jsonlines.open('repo_data/german_eval_data.jsonl', 'w') as writer:
    writer.write_all(german_eval_data)
