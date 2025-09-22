import os
import sys
from generation.src.utils import test_pipeline
from parse import format_sents, parse_sents
from evaluate import get_parse_accuracy
from prompts.prompt import prompt_from_grammar


def get_safe_filename(filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(new_filename):
        new_filename = f"{base}-{counter}{ext}"
        counter += 1
    return new_filename


def generate_from_prompt(prompt, n_prompts):
    response_path = "prompts/prompt-newest"

    suffix = (
        f"-{n_prompts}-responses.txt" if n_prompts > 1 else "-response.txt"
    )
    response_path = (
        response_path.split(".")[0] + suffix
    )

    response_path = get_safe_filename(response_path)

    test_pipeline(
        prompt,
        response_path,
        n_prompts
    )

    return response_path


def main():
    grammar_path = sys.argv[1]
    n_prompts = int(sys.argv[2])
    assert grammar_path.endswith(".irtg"), "Provide IRTG grammar"
    assert isinstance(n_prompts, int), "Provide no. of times to prompt"

    prompt = prompt_from_grammar(grammar_path, n_sets=1, k=10)
    print(prompt)

    response_path = generate_from_prompt(prompt, n_prompts)

    sents_path = format_sents(response_path)
    varfree_path = parse_sents(sents_path, grammar_path)
    get_parse_accuracy(varfree_path, grammar_path)


if __name__ == "__main__":
    main()
