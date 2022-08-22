import argparse
from datasets import load_dataset, interleave_datasets
from transformers import RobertaTokenizerFast, AutoTokenizer
import json
import shutil
import os
import re


def preprocess_yields(yields):
    arr = []
    for element in yields:
        arr.append(element["text"])
    return arr


def truncate(example):
    max_size = 256
    example["text"] = example["text"].split(" ")[:max_size]
    example["text"] = " ".join(example["text"])
    return example


def get_training_corpus(args, dataset):
    for start_idx in range(0, args.corpus_size, 1000):
        arr = []
        for i in range(1000):
            arr.append(next(dataset)["text"])
        yield arr


def create_merge_files(args, corpus):
    old_tokenizer = RobertaTokenizerFast.from_pretrained("roberta-base", cache_dir=f"{args.output}/cache")
    tokenizer = old_tokenizer.train_new_from_iterator(corpus, args.merge_size)
    tokenizer.save_pretrained(f"{args.output}/oscar_tokenizer")

    new_vocab_tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base", cache_dir=f"{args.output}/cache")
    new_vocab_tokenizer.add_tokens(list(tokenizer.get_vocab().keys()))
    new_vocab_tokenizer.save_pretrained(f"{args.output}/new_vocab_tokenizer")

    base_tokens = json.load(open(f"{args.output}/new_vocab_tokenizer/vocab.json", encoding="utf-8"))
    added_tokens = json.load(open(f"{args.output}/new_vocab_tokenizer/added_tokens.json", encoding="utf-8"))

    added_tokens = dict(sorted(added_tokens.items(), key=lambda item: item[1]))

    combined_vocab = base_tokens.copy()
    combined_vocab.update(added_tokens)

    with open(f'{args.output}/vocab.json', 'w', encoding='utf-8') as file:
        json.dump(combined_vocab, file, ensure_ascii=False)

    combined_tokenizer = RobertaTokenizerFast(vocab_file=f"{args.output}/vocab.json",
                                              merges_file=f"{args.output}/oscar_tokenizer/merges.txt",
                                              model_max_length=old_tokenizer.model_max_length)
    combined_tokenizer.save_pretrained(f"{args.output}/combined_tokenizer_c{args.corpus_size/1000000.0}M_m{args.merge_size//1000}K")
    shutil.rmtree(f"{args.output}/oscar_tokenizer")
    shutil.rmtree(f"{args.output}/new_vocab_tokenizer")
    os.remove(f'{args.output}/vocab.json')


def main():
    parser = argparse.ArgumentParser(description="Combine two datasets to produce a merge file")

    parser.add_argument("--language1", type=str, required=True)
    parser.add_argument("--language2", type=str, required=True)
    parser.add_argument("--output", type=str, default=".")
    parser.add_argument("--corpus_size", type=int, default=1000000)
    parser.add_argument("--merge_size", type=int, default=50256)

    args = parser.parse_args()

    subset1 = load_dataset('oscar', "unshuffled_deduplicated_" + args.language1, split='train', streaming=True)
    subset2 = load_dataset('oscar', "unshuffled_deduplicated_" + args.language2, split='train', streaming=True)

    subset1 = subset1.shuffle(buffer_size=args.corpus_size/100)
    subset2 = subset2.shuffle(buffer_size=args.corpus_size/100)
    multilingual_dataset = interleave_datasets([subset1, subset2])
    multilingual_dataset = multilingual_dataset.remove_columns("id")
    multilingual_dataset = multilingual_dataset.map(truncate)

    multilingual_dataset = multilingual_dataset.filter(lambda example: not re.search(r'(.)\1{2}', example["text"]))

    multilingual_dataset = iter(multilingual_dataset)
    training_corpus = get_training_corpus(args, multilingual_dataset)
    create_merge_files(args, training_corpus)


if __name__ == "__main__":
    main()
