import requests
import time
import json
import jsonpickle
from tqdm import tqdm
import base64
import urlfetch
from tree_sitter import Language, Parser

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


headers = {
    'User-Agent': 'Github Scraper',
    'Authorization': 'Token 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'
}
star_count = 9
id_set = jsonpickle.decode(json.load((open(f"filtered_starcount_{star_count+1}_repo_list.json"))))
test_set = jsonpickle.decode(json.load((open("repo_name_list.json"))))
docs_and_funcs = dict()

for repo_name in test_set:
    for page_index in range(100):
        url = f"https://api.github.com/search/code?q=repo:{repo_name}+extension:java+in:file+language:java&per_page=100&page={page_index}"
        response = requests.get(url, headers=headers).json()
        if response.status_code == 200:
            for git_url in response["items"]["git_url"]:
                result = urlfetch.fetch(git_url)
                if result.status_code == 200:
                    data = json.loads(result.content)
                    decoded_content = base64.b64decode(data["content"])
                else:
                    print(result.status_code)
        else:
            print(f"For id {repo_id} this error happened: {response.json()['message']}")


get_docs_and_strings()
