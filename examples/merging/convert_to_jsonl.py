import os
os.chdir("../..")
from convokit import Corpus
os.chdir("./examples/merging")
import re

def convert_json_to_jsonl_safe(corpus_filepath):
    corpus = Corpus(filename=corpus_filepath)
    corpus.dump(name=corpus_filepath, save_to_existing_path=True)

def convert_json_to_jsonl_fast(filepath):
    """
    :param filepath: Path to utterances.json
    """
    with open(filepath, 'r') as f:
        json_str = f.read()

    json_str = json_str[1:-1] #strip [ ]

    jsonl_filepath = filepath.replace(".json", ".jsonl")

    with open(jsonl_filepath, 'w') as f:
        bracket_ctr = 0
        utt_acc = ''
        ignore_chars = 0

        for c in json_str:
            if ignore_chars > 0:
                ignore_chars -= 1
                continue

            utt_acc += c

            if c == '{':
                bracket_ctr += 1
            elif c == '}':
                bracket_ctr -= 1
                if bracket_ctr == 0:
                    f.write(utt_acc)
                    f.write("\n")
                    utt_acc = ''
                    ignore_chars = 2

def convert_json_to_jsonl_regex(filepath):
    pattern = re.compile(r'({"id":.+?"timestamp":.+?})')
    with open(filepath, 'r') as f:
        json_str = f.read()

    jsonl_filepath = filepath.replace(".json", ".jsonl")
    with open(jsonl_filepath, 'w') as f:
        for match in re.findall(pattern, json_str):
            f.write(match)
            f.write("\n")

if __name__ == "__main__":
    os.chdir("temp-corpus")
    convert_json_to_jsonl_regex("utterances.json")
    os.chdir("..")
    corpus1 = Corpus(filename="temp-corpus")
    print(corpus1.utterances)

