from itertools import chain
from datasets import load_dataset, load_from_disk
from transformers import AutoTokenizer
import argparse


def main():
    parser = argparse.ArgumentParser(description="Combine two datasets to produce a merge file")

    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--tokenizer", type=str, required=True)
    parser.add_argument("--output_dir", type=str, default=".")

    args = parser.parse_args()
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    raw_dataset = load_from_disk(args.dataset)
    max_seq_length = args.tokenizer.model_max_length
    column_names = raw_dataset["train"].column_names

    def tokenize_function(examples):
        return tokenizer(examples["text"], return_special_tokens_mask=True)

    tokenized_datasets = raw_dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=column_names,
        desc="Running tokenizer on every text in dataset",
    )

    def group_texts(examples):
        # Concatenate all texts.
        concatenated_examples = {k: list(chain(*examples[k])) for k in examples.keys()}
        total_length = len(concatenated_examples[list(examples.keys())[0]])
        # We drop the small remainder, we could add padding if the model supported it instead of this drop, you can
        # customize this part to your needs.
        if total_length >= max_seq_length:
            total_length = (total_length // max_seq_length) * max_seq_length
        # Split by chunks of max_len.
        result = {
            k: [t[i: i + max_seq_length] for i in range(0, total_length, max_seq_length)]
            for k, t in concatenated_examples.items()
        }
        return result

    tokenized_datasets = tokenized_datasets.map(
        group_texts,
        batched=True,
        desc=f"Grouping texts in chunks of {max_seq_length}",
    )

    tokenized_datasets.save_to_disk(args.output_dir)


if __name__ == "__main__":
    main()
