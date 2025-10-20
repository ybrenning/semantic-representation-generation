import argparse
import json
import numpy as np

from generation.utils import test_pipeline
from parse import format_sents, parse_sents
from evaluate import (
    get_non_null_lines,
    get_non_rep_lines,
    get_consistent_lines,
    get_accuracies
)
from generation.prompt import prompt_from_grammar, get_pp_rec_prompt
from utils import get_safe_filename, en_header, create_out_path
from postprocess import postprocess_varfree


def generation_loop(
    dataset_type,
    grammar_path,
    n_prompts,
    n_sets,
    verbose=False
):
    responses = ""
    for _ in range(n_prompts):
        # Maybe also save the generated prompts?
        # prompt = prompt_from_grammar(
        #     grammar_path,
        #     n_sets=n_sets,
        #     k=30
        # )
        prompt = get_pp_rec_prompt(2, 4)

        response = test_pipeline(
            prompt,
            temperature=0.5,
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
        "dataset_type",
        choices=["batch", "slog"],
        help="Type of generation to attempt (batch or slog)"
    )
    parser.add_argument(
        "grammar_path",
        type=str,
        help="Path to the IRTG grammar file"
    )
    parser.add_argument(
        "n_prompts",
        type=int,
        help="Number of times to prompt the model"
    )
    parser.add_argument(
        "n_batches",
        type=int,
        help="Number of batches per prompt"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    if not args.grammar_path.endswith(".irtg"):
        parser.error("The grammar file must have a .irtg extension")

    return args


def main():

    sent_type_grammars = [
        "grammars/g1.irtg",
        "grammars/g2.irtg",
        "grammars/g3.irtg",
        "grammars/g4.irtg",
        "grammars/g5.irtg",
        "grammars/g6.irtg"
    ]
    args = parse_args()
    dataset_type = args.dataset_type
    grammar_path = args.grammar_path
    n_prompts = args.n_prompts
    n_batches = args.n_batches
    verbose = args.verbose

    if dataset_type == "batch":
        batch_size = 6
    elif dataset_type == "slog":
        batch_size = 2

    n_sents = n_prompts * n_batches * batch_size

    metrics = {}

    oov_pct_total_list = []
    oov_pct_sent_list = []
    accs_list = []
    rep_accs_list = []
    consistent_accs_list = []
    n_loops = 0
    metrics["dataset_type"] = dataset_type
    metrics["n_prompts"] = n_prompts
    metrics["n_batches"] = n_batches
    metrics["n_sents"] = n_sents
    english, semantics = [], []
    while len(semantics) != (n_batches*n_prompts):
        # Generation step
        response_path = generation_loop(
            dataset_type,
            grammar_path,
            n_prompts,
            n_batches,
            verbose=verbose
        )

        assert 0
        # Format and parse model outputs
        format_sents(response_path, verbose=verbose)
        oov_pct_total, oov_pct_sent = parse_sents(
            response_path,
            grammar_path,
            sent_type_grammars,
            batch_size=batch_size,
            verbose=verbose
        )

        # Evaluate and filter
        # TODO: Put all this in an eval block
        oov_pct_total_list.append(oov_pct_total)
        oov_pct_sent_list.append(oov_pct_sent)

        non_null_lines = get_non_null_lines(response_path, grammar_path)
        accs = get_accuracies(non_null_lines, verbose=verbose)
        accs_list.append(accs)

        consistent_lines = get_consistent_lines(response_path, non_null_lines)
        consistent_accs = get_accuracies(consistent_lines, verbose=verbose)
        consistent_accs_list.append(consistent_accs)

        non_rep_lines = get_non_rep_lines(response_path, consistent_lines)
        rep_accs = get_accuracies(non_rep_lines, verbose=verbose)
        rep_accs_list.append(rep_accs)

        # Filtering step
        valid_batches = rep_accs.all(axis=0)
        en_lines = []
        vf_lines = []
        for i in range(0, 6):
            en_lines_cur = []
            vf_lines_cur = []
            sent_path = create_out_path(
                f"output/english/{i + 1}",
                response_path,
                check_exists=False,
                ext=".txt"
            )
            varfree_path = create_out_path(
                f"output/varfree_lf/{i + 1}",
                response_path,
                check_exists=False,
                ext=".txt"
            )

            with open(sent_path, "r") as f:
                en_lines_cur = np.array([
                    line for line in f.readlines()
                    if line.strip() and not line.startswith("//")
                ], dtype=object)

            with open(varfree_path, "r") as f:
                vf_lines_cur = np.array(f.readlines(), dtype=object)

            en_lines.append(en_lines_cur[valid_batches])
            vf_lines.append(vf_lines_cur[valid_batches])

        en_lines = np.array(en_lines, dtype=object).T.tolist()
        vf_lines = np.array(vf_lines, dtype=object).T.tolist()

        if not english and not semantics:
            english = list(en_lines)
            semantics = list(vf_lines)
        else:
            remainder = n_batches*n_prompts - len(semantics)
            assert remainder > 0
            english.extend(en_lines[:remainder])
            semantics.extend(vf_lines[:remainder])

        n_loops += 1
        print("Generated", len(semantics), "/", n_batches*n_prompts)

    sent_path = create_out_path(
        "data/english", response_path, check_exists=True, ext=".txt"
    )
    varfree_path = create_out_path(
        "data/varfree_lf", response_path, check_exists=True, ext=".txt"
    )

    with open(sent_path, "w") as f:
        f.write(
            en_header + "".join(line for batch in english for line in batch)
        )
        print("Saved sentences to", sent_path)

    with open(varfree_path, "w") as f:
        f.write("".join(line for batch in semantics for line in batch))
        print("Saved representations to", varfree_path)

    assert (
        len(oov_pct_total_list) == len(oov_pct_sent_list) == n_loops
    )
    metrics["oov_pct_total"] = oov_pct_total_list
    metrics["oov_pct_sent"] = oov_pct_sent_list
    metrics["accs"] = accs_list
    metrics["consistent_accs"] = consistent_accs_list
    metrics["rep_accs"] = rep_accs_list
    metrics["n_loops"] = n_loops

    metrics_path = create_out_path(
        "data/metrics", response_path, check_exists=True, ext=".json"
    )

    with open(metrics_path, "w") as f:
        json.dump(metrics, f)
        print("Saved scores to", metrics_path)

    # Postprocessing step
    postprocess_varfree(sent_path, varfree_path, verbose=verbose)


if __name__ == "__main__":
    main()
