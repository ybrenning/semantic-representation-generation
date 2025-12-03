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
from generation.prompt import prompt_from_grammar
from utils import (
    get_safe_filename,
    en_header,
    create_out_path,
    grammars_from_dataset
)
from postprocess import postprocess_varfree


slog_datasets = [
    "slog-rec_pp",
    "slog-rec_cp",
    "slog-rec_center_emb",
    ...

    # TODO: Implement each SLOG generalization case.
    # Note that this would necessitate a separate control grammar
    # for each type of dataset
]


def generation_loop(
    dataset_type,
    grammar_path,
    n_prompts,
    n_batches,
    depth_train=None,
    depth_gen=None,
    verbose=False,
):
    responses = ""
    for _ in range(n_prompts):
        # Maybe also save the generated prompts?
        prompt = prompt_from_grammar(
            dataset_type,
            grammar_path,
            n_batches=n_batches,
            k=30,
            rec_depth=depth_train,
        )

        response = test_pipeline(
            prompt,
            temperature=0.5,
            top_p=0.9,
            verbose=verbose
        )
        responses += response + "\n"

    # SLOG-like dataset - run second prompt loop w/ recursion depth
    # TODO: Handle non-recursive SLOG-like datasets
    if depth_gen is not None:
        for _ in range(n_prompts):
            prompt = prompt_from_grammar(
                dataset_type,
                grammar_path,
                n_batches=n_batches,
                k=30,
                rec_depth=depth_gen,
            )

            response = test_pipeline(
                prompt,
                temperature=0.5,
                top_p=0.9,
                verbose=verbose
            )
            responses += response + "\n"

    response_path = f"generation/responses/{dataset_type}"

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
        choices=["batch", "batch-prev"] + slog_datasets,
        help="Type of generation to attempt (batch or slog)"
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
        "-rt", "--rec_depth_train",
        type=int,
        help="Recursion depth for train sentences"
    )
    parser.add_argument(
        "-rg", "--rec_depth_gen",
        type=int,
        help="Recursion depth for generalization sentences"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    if (
        "rec" in args.dataset_type and
        (not args.rec_depth_train or not args.rec_depth_gen)
    ):
        parser.error(
            "Specify recursion depths for train and generalization (-rt -rg)"
        )
    if (
        "rec" not in args.dataset_type and
        (args.rec_depth_train or args.rec_depth_gen)
    ):
        parser.error(
            "Recursion depths provided for non-recursive dataset"
        )

    return args


def main():
    args = parse_args()
    dataset_type = args.dataset_type
    n_prompts = args.n_prompts
    n_batches = args.n_batches
    rec_depth_train = args.rec_depth_train
    rec_depth_gen = args.rec_depth_gen
    verbose = args.verbose

    prompt_grammar, control_grammars = grammars_from_dataset(
        dataset_type,
        rec_depth_train,
        rec_depth_gen
    )
    batch_size = len(control_grammars)

    sents_per_batch = n_prompts * n_batches
    n_sents_total = sents_per_batch * batch_size

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
    metrics["n_sents_total"] = n_sents_total
    english, semantics = [], []
    while len(semantics) != (n_batches*n_prompts):
        # Generation step
        response_path = generation_loop(
            dataset_type,
            prompt_grammar,
            n_prompts,
            n_batches,
            depth_train=rec_depth_train,
            depth_gen=rec_depth_gen,
            verbose=verbose
        )

        # Format and parse model outputs
        format_sents(
            dataset_type,
            response_path,
            batch_size,
            n_batches,
            n_prompts,
            verbose=verbose,
            save=True
        )

        oov_pct_total, oov_pct_sent = parse_sents(
            response_path,
            prompt_grammar,
            control_grammars,
            batch_size,
            verbose=verbose,
            save=True
        )

        # Evaluate and filter
        # TODO: Put all this in an eval block
        oov_pct_total_list.append(oov_pct_total)
        oov_pct_sent_list.append(oov_pct_sent)

        non_null_lines = get_non_null_lines(
            response_path, batch_size
        )

        print("Parse accuracies")
        accs = get_accuracies(non_null_lines, verbose=verbose)
        accs_list.append(accs)

        if dataset_type.startswith("batch"):
            consistent_lines = get_consistent_lines(
                response_path, non_null_lines, batch_size, verbose=verbose
            )
            print("Sentences w/ consistent main S/V")
            consistent_accs = get_accuracies(consistent_lines, verbose=verbose)
            consistent_accs_list.append(consistent_accs)
        else:
            consistent_lines = non_null_lines

        non_rep_lines = get_non_rep_lines(
            response_path, consistent_lines, batch_size
        )
        print("Non-repetition sentences")
        rep_accs = get_accuracies(non_rep_lines, verbose=verbose)
        rep_accs_list.append(rep_accs)

        # Filtering step
        valid_batches = non_rep_lines.all(axis=0)
        en_lines = []
        vf_lines = []
        for i in range(0, batch_size):
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
