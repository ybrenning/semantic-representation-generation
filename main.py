import os
import sys
from generation.src.utils import test_pipeline
from parse import format_sents, parse_sents
from evaluate import get_parse_accuracy


def get_safe_filename(filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(new_filename):
        new_filename = f"{base}-{counter}{ext}"
        counter += 1
    return new_filename


def generate_from_prompt(prompt_path):
    with open(prompt_path, "r") as f:
        prompt = f.read()

    response_path = (
        prompt_path.split(".")[0] + "-response.txt"
    )

    response_path = get_safe_filename(response_path)

    test_pipeline(
        prompt,
        response_path
    )

    return response_path


def main():
    prompt_path = sys.argv[1]
    grammar_path = sys.argv[2]
    assert prompt_path.endswith(".txt")
    assert grammar_path.endswith(".irtg")

    response_path = generate_from_prompt(prompt_path)
    sents_path = format_sents(response_path)
    varfree_path = parse_sents(sents_path, grammar_path)
    get_parse_accuracy(varfree_path)


if __name__ == "__main__":
    main()
