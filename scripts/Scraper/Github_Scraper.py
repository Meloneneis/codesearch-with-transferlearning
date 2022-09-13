import argparse
import itertools
import tqdm
import requests
import time
import json
import jsonpickle
from tqdm import tqdm
import base64
import urlfetch
from tree_sitter import Language, Parser
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
langparser = Parser()
langparser.set_language(JAVA_LANGUAGE)

method_query = JAVA_LANGUAGE.query("""
(
  (method_declaration) @method
)
""")


# gets all possible combinations of queries in the given size
def query_combinator(args):
    queries = args.queries.split(',')
    return [' '.join(subset) for subset in itertools.combinations(queries, args.query_size)]


def main():
    argparser = argparse.ArgumentParser(description="Combine two datasets to produce a merge file")

    argparser.add_argument("--lang", type=str, required=True)
    argparser.add_argument("--queries", default="", type=str, required=True)
    argparser.add_argument("--query_size", type=int, default=3)
    argparser.add_argument("--starcount", type=int, default=5)
    argparser.add_argument("--output", default="")
    argparser.add_argument("--spokenlanguage", default="de")
    argparser.add_argument("--auth_token", type=str, required=True)
    argparser.add_argument("--existing_dataset", type=str, default=None)
    args = argparser.parse_args()

    queries = query_combinator(args)
    headers = {
        'User-Agent': 'Github Scraper',
        'Authorization': f'Token {args.auth_token}'
    }
    repo_names = set()
    page_index = 9

    # get all possible repos from queries
    for query in tqdm(queries, desc="Queries processed"):
        status = True
        while status:
            url = f"https://api.github.com/search/code?q={query}+in:file +language:{args.lang}&per_page=100&page=" \
                  f"{page_index}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                for repository in response.json()["items"]:
                    repo_names.add(repository["repository"]["full_name"])
                time.sleep(90)
                page_index += 1
            else:
                status = False

    # filter repos by starcount and by spoken language
    remove_set = set()
    for repo in tqdm(repo_names, desc="Filterprogress of repos"):
        status = True
        german_test = 0
        noDocCounter = 0
        while status:
            url = f"https://api.github.com/repos/{repo}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                if response.json()["stargazers_count"] < args.starcount:
                    remove_set.add(repo)
                    status = False
                else:
                    # check if repo is spoken language
                    repo_request = requests.get(
                        f"https://api.github.com/repos/{repo}/git/trees/master?recursive=1", headers=headers)
                    repo_json = repo_request.json() if repo_request.status_code == 200 else print(
                        repo_request.status_code)
                    if repo_request.status_code is not 200:
                        status = False
                        continue
                    java_files = [file for file in repo_json["tree"] if file["path"].endswith(".java")]
                    for file in java_files:
                        if noDocCounter > 50 or not status:
                            status = False
                            break
                        time.sleep(0.1)
                        try:
                            result = urlfetch.fetch(file["url"], headers=headers)
                            data = json.loads(result.content) if result.status_code == 200 else print(
                                result.status_code)
                            decoded_content = base64.b64decode(data["content"])
                            tree = langparser.parse(bytes(decoded_content))
                            method_captures = method_query.captures(tree.root_node)
                            for capture in method_captures:
                                if not status:
                                    break
                                if capture[0].prev_sibling.type == "doc_comment" or capture[0].next_sibling.type == \
                                        "doc_comment":
                                    docstring = capture[0].prev_sibling.text.decode("ISO-8859-1") if \
                                        capture[0].prev_sibling.type == "doc_comment" else \
                                        capture[0].next_sibling.text.decode("ISO-8859-1")
                                    if langdetect.detect(docstring) != args.spokenlanguage:
                                        german_test -= 1
                                        print(german_test, end=" ")
                                        if german_test < -5:
                                            print(f"{repo} removed, because not {args.spokenlanguage}")
                                            remove_set.add(repo)
                                            status = False
                                        break
                                    german_test += 1
                                    print(german_test, end=" ")
                                    noDocCounter = 0
                                    time.sleep(0.1)
                                    if german_test > 5:
                                        status = False
                                else:
                                    noDocCounter += 1
                                    if noDocCounter == 50:
                                        print("no docs found.. skip repo..")
                                    continue
                        except:
                            pass
            else:
                status = False
    for repo in remove_set:
        repo_names.remove(repo)
    json_set = jsonpickle.encode(repo_names)
    with open("repo_data/german_repos.json", "w") as f:
        json.dump(json_set, f)


if __name__ == "__main__":
    main()
