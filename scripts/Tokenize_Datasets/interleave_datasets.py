from datasets import load_dataset, interleave_datasets, DatasetDict
import re
import argparse


def map_doc_and_func(example):
    example["text"] = example["func_documentation_string"] + "<c>" + example["whole_func_string"]
    return example


def main():
    parser = argparse.ArgumentParser(description="Combine two datasets to produce a merge file")

    parser.add_argument("--datasets", type=str, required=True, help="Input string and datasets delimited by ,")
    parser.add_argument("--configs", type=str, required=True, help="Input string and configs delimited by ,")
    parser.add_argument("--validation_split_percentage", type=int, default=5)
    parser.add_argument("--distribution", type=str, required=True, help="Input string and distribution delimited by ,")
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
                dataset_list[i][split] = dataset_list[i][split].map(map_doc_and_func)
                dataset_list[i][split] = dataset_list[i][split].remove_columns([col for col in dataset_list[i][split].column_names if col != "text"])

    interleaved_train_dataset = interleave_datasets([x["train"] for x in dataset_list], probabilities=distribution)
    interleaved_validation_dataset = interleave_datasets([x["validation"] for x in dataset_list], probabilities=distribution)
    interleaved_dataset = DatasetDict({"train": interleaved_train_dataset, "validation": interleaved_validation_dataset})
    string_name = "-".join(f"{x}{y}" for (x, y) in zip(datasets, distribution))
    interleaved_dataset.save_to_disk(f"{args.output_dir}{string_name}-trainvalid-dataset")


if __name__ == "__main__":
    main()
