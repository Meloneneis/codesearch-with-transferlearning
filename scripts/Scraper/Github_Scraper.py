import argparse
import requests


def request_pages(args):
    page_index = 1
    url = f"https://api.github.com/search/code?q={args.query} +in:file +language:{args.lang}&per_page=100&page=\
    {page_index}"
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Token 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'
    }

    response = requests.request("GET", url, headers=headers).json()

    for page_index in range(3):
        id_set = set()
        for item in response.json()["items"]:
            id_set.add(item["repository"]["id"])

        return None


def main():
    parser = argparse.ArgumentParser(description="Combine two datasets to produce a merge file")

    parser.add_argument("--lang", type=str, required=True)
    parser.add_argument("--query", type=str, required=True)
    parser.add_argument("--starcount", type=int, default=2)
    parser.add_argument("--output")
    args = parser.parse_args()
    request_pages(args)


if __name__ == "__main__":
    main()
