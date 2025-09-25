import argparse

from generation.src.utils import test_pipeline
from parse import format_sents, parse_sents
from evaluate import evaluate_parse
from generation.prompt import prompt_from_grammar
from postprocess import (
    handle_null_sents,
    handle_incorrect_sents,
    handle_repetition_sents
)
from utils import get_safe_filename, en_header


def generation_loop(grammar_path, n_prompts, n_sets, verbose=False):
    responses = ""
    for _ in range(n_prompts):
        # Maybe also save the generated prompts?
        prompt = prompt_from_grammar(
            grammar_path,
            n_sets=n_sets,
            k=30
        )

        response = test_pipeline(
            prompt,
            temperature=0.4,
            top_p=0.9,
            verbose=verbose
        )
        responses += response + "\n"

    response_path = "generation/responses/prompt-newest"

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
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output."
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
    verbose = args.verbose

    n_sents = n_prompts * n_sets * 6
    english, semantics = [], []
    while len(semantics) != n_sents:
        # Generation step
        response_path = generation_loop(
            grammar_path,
            n_prompts,
            n_sets,
            verbose
        )

        # Format and parse steps
        sent_path = format_sents(response_path)
        varfree_path = parse_sents(sent_path, grammar_path)

        # Evaluation step
        evaluate_parse(
            varfree_path,
            grammar_path,
            show_stats=True,
            show_oov=verbose
        )

        # Filtering step
        en_lines, vf_lines = handle_null_sents(sent_path, varfree_path)
        en_lines, vf_lines, n_incorrect = handle_incorrect_sents(
            en_lines, vf_lines
        )
        en_lines, vf_lines, n_repetitions = handle_repetition_sents(
            en_lines, vf_lines
        )

        if not english and not semantics:
            english = en_lines.copy()
            semantics = vf_lines.copy()
        else:
            remainder = n_sents - len(semantics)
            assert remainder > 0
            english.extend(en_lines[:remainder])
            semantics.extend(vf_lines[:remainder])

        print("Generated", len(semantics), "/", n_sents)

    sent_path_out = "data/english/" + sent_path.split("/")[-1]
    varfree_path_out = "data/varfree_lf/" + sent_path.split("/")[-1]

    with open(sent_path_out, "w") as f:
        f.write(en_header + "".join(english))
        print("Saved sentences to", sent_path_out)

    with open(varfree_path_out, "w") as f:
        f.write("".join(semantics))
        print("Saved representations to", varfree_path_out)

    # Postprocessing step
    ...


if __name__ == "__main__":
    main()
