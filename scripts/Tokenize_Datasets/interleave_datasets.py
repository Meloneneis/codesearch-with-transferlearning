from datasets import load_dataset, interleave_datasets, DatasetDict
import re
import argparse
from io import StringIO
import tokenize


def remove_comments_and_docstrings(source,lang):
    if lang in ['python']:
        """
        Returns 'source' minus comments and docstrings.
        """
        io_obj = StringIO(source)
        out = ""
        prev_toktype = tokenize.INDENT
        last_lineno = -1
        last_col = 0
        for tok in tokenize.generate_tokens(io_obj.readline):
            token_type = tok[0]
            token_string = tok[1]
            start_line, start_col = tok[2]
            end_line, end_col = tok[3]
            ltext = tok[4]
            if start_line > last_lineno:
                last_col = 0
            if start_col > last_col:
                out += (" " * (start_col - last_col))
            # Remove comments:
            if token_type == tokenize.COMMENT:
                pass
            # This series of conditionals removes docstrings:
            elif token_type == tokenize.STRING:
                if prev_toktype != tokenize.INDENT:
            # This is likely a docstring; double-check we're not inside an operator:
                    if prev_toktype != tokenize.NEWLINE:
                        if start_col > 0:
                            out += token_string
            else:
                out += token_string
            prev_toktype = token_type
            last_col = end_col
            last_lineno = end_line
        temp=[]
        for x in out.split('\n'):
            if x.strip()!="":
                temp.append(x)
        return '\n'.join(temp)
    elif lang in ['ruby']:
        return source
    else:
        def replacer(match):
            s = match.group(0)
            if s.startswith('/'):
                return " " # note: a space and not an empty string
            else:
                return s
        pattern = re.compile(
            r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
            re.DOTALL | re.MULTILINE
        )
        temp=[]
        for x in re.sub(pattern, replacer, source).split('\n'):
            if x.strip()!="":
                temp.append(x)
        return '\n'.join(temp)


def map_doc_and_func(example):
    try:
        filtered_func = remove_comments_and_docstrings(example["whole_func_string"], example["language"])
        example["text"] = example["func_documentation_string"] + "<c>" + filtered_func
    except:
        example["text"] = None
    return example


def main():
    parser = argparse.ArgumentParser(description="Combine two datasets to produce a merge file")

    parser.add_argument("--datasets", type=str, default="code_search_net", help="Input string and datasets delimited by ,")
    parser.add_argument("--configs", type=str, default="all", help="Input string and configs delimited by ,")
    parser.add_argument("--validation_split_percentage", type=int, default=5)
    parser.add_argument("--distribution", type=str, default="1", help="Input string and distribution delimited by ,")
    parser.add_argument("--cache_dir", type=str, default=None)
    parser.add_argument("--output_dir", type=str, default="")

    args = parser.parse_args()
    datasets = args.datasets.split(',')
    configs = [string if string != "None" else None for string in args.configs.split(",")]
    distribution = [float(item) for item in args.distribution.split(',')]
    dataset_list = []
    num_datasets = len(datasets)
    for i in range(num_datasets):
        dataset_list.append(load_dataset(datasets[i], configs[i], cache_dir=args.cache_dir))
        if datasets[i] != "code_search_net":
            if "validation" not in dataset_list[i].keys():
                dataset_list[i]["validation"] = load_dataset(
                    datasets[i],
                    configs[i],
                    split=f"train[:{args.validation_split_percentage}%]",
                    cache_dir=args.cache_dir,
                )
                dataset_list[i]["train"] = load_dataset(
                    datasets[i],
                    configs[i],
                    split=f"train[{args.validation_split_percentage}%:]",
                    cache_dir=args.cache_dir,
                )
            for split in dataset_list[i]:
                dataset_list[i][split] = dataset_list[i][split].filter(lambda example: not re.search(r'(.)\1{2}', example["text"]))
                dataset_list[i][split] = dataset_list[i][split].remove_columns([col for col in dataset_list[i][split].column_names if col != "text"])
        else:
            for split in dataset_list[i]:
                text_column = ["Placeholder"] * len(dataset_list[i][split])
                dataset_list[i][split] = dataset_list[i][split].add_column("text", text_column)
                dataset_list[i][split] = dataset_list[i][split].map(map_doc_and_func, load_from_cache_file=False)
                dataset_list[i][split] = dataset_list[i][split].remove_columns([col for col in dataset_list[i][split].column_names if col != "text"])
                dataset_list[i][split] = dataset_list[i][split].filter(lambda example: example["text"] is not None)

    interleaved_train_dataset = interleave_datasets([x["train"] for x in dataset_list], probabilities=distribution)
    interleaved_validation_dataset = interleave_datasets([x["validation"] for x in dataset_list], probabilities=distribution)
    interleaved_dataset = DatasetDict({"train": interleaved_train_dataset, "validation": interleaved_validation_dataset})
    string_name = "-".join(f"{x}{y}" for (x, y) in zip(datasets, distribution))
    interleaved_dataset.save_to_disk(f"{args.output_dir}/{string_name}-trainvalid-dataset")


if __name__ == "__main__":
    main()
