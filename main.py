import argparse

from generation.src.utils import test_pipeline
from parse import format_sents, parse_sents
from evaluate import evaluate_parse
from prompts.prompt import prompt_from_grammar
from preprocess import (
    handle_null_sents,
    handle_incorrect_sents,
    handle_repetition_sents
)
from utils import get_safe_filename


def generation_loop(grammar_path, n_prompts, n_sets):
    responses = ""
    for _ in range(n_prompts):
        # Maybe also save the generated prompts?
        prompt = prompt_from_grammar(
            grammar_path,
            n_sets=n_sets,
            k=30
        )
        print(prompt)

        response = test_pipeline(
            prompt,
            temperature=0.4,
            top_p=0.9
        )
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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Execute data generation pipeline"
    )
    parser.add_argument(
        "grammar_path",
        type=str,
        help="Path to the IRTG grammar file (.irtg)."
    )
    parser.add_argument(
        "n_prompts",
        type=int,
        help="Number of times to prompt."
    )
    parser.add_argument(
        "n_sets",
        type=int,
        help="Number of sentence sets per prompt"
    )

    args = parser.parse_args()

    if not args.grammar_path.endswith(".irtg"):
        parser.error("The grammar file must have a .irtg extension")

    return args


def main():
    args = parse_args()
    grammar_path = args.grammar_path
    n_prompts = args.n_prompts
    n_sets = args.n_sets

    # Generation step
    response_path = generation_loop(grammar_path, n_prompts, n_sets)

    # Format and parse steps
    sent_path = format_sents(response_path)
    varfree_path = parse_sents(sent_path, grammar_path)

    # Filtering step
    en_lines, vf_lines = handle_null_sents(sent_path, varfree_path)
    en_lines, vf_lines = handle_incorrect_sents(en_lines, vf_lines)
    en_lines, vf_lines = handle_repetition_sents(en_lines, vf_lines)

    # Evaluation step
    evaluate_parse(
        varfree_path,
        grammar_path,
        show_stats=True,
        show_oov=True
    )
    assert 0

    # Postprocessing step


if __name__ == "__main__":
    main()
