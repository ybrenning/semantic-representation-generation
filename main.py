import os
import sys
from generation.src.utils import test_pipeline
from parse import format_sents, parse_sents
from evaluate import get_parse_accuracy
from prompts.prompt import prompt_from_grammar
from utils import get_safe_filename


def generation_loop(grammar_path, n_prompts):
    responses = ""
    for _ in range(n_prompts):
        prompt = prompt_from_grammar(grammar_path, n_sets=3, k=20)
        print(prompt)

        response = test_pipeline(prompt, temperature=0.4, top_p=0.9)
        responses += response + "\n"

    response_path = "prompts/prompt-newest"

    suffix = (
        f"-{n_prompts}-responses.txt" if n_prompts > 1 else "-response.txt"
    )
    response_path = (
        response_path.split(".")[0] + suffix
    )

    response_path = get_safe_filename(response_path)

    with open(response_path, "w") as f:
        f.write(responses)
        print("Saved response(s) to", response_path)

    return response_path


def main():
    grammar_path = sys.argv[1]
    n_prompts = int(sys.argv[2])
    assert grammar_path.endswith(".irtg"), "Provide IRTG grammar"
    assert isinstance(n_prompts, int), "Provide no. of times to prompt"

    response_path = generation_loop(grammar_path, n_prompts)

    sents_path = format_sents(response_path)
    varfree_path = parse_sents(sents_path, grammar_path)
    get_parse_accuracy(varfree_path, grammar_path)


if __name__ == "__main__":
    main()
