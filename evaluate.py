import argparse
import re
import numpy as np
from tabulate import tabulate
from utils import create_out_path


DET = ["the", "a"]
AUX = ["was"]
BY = ["by"]
INF = ["to"]
REL_PRON = ["that"]
PP_LOC = ["on", "in", "beside"]


def get_accuracies(valid_lines, verbose=False):
    # Accuracy per sentence type
    sent_accs = valid_lines.mean(axis=1)

    # Accuracy of batches
    batch_acc = valid_lines.all(axis=0).mean()

    accs = {}
    accs["sent_accs"] = sent_accs.tolist()
    accs["batch_acc"] = batch_acc.item()

    if verbose:
        headers = ["Sentence Type", "Accuracy"]
        table = [
            (f"Type {i+1}", f"{acc:.2%}") for i, acc in enumerate(sent_accs)
        ]
        print(tabulate(table, headers=headers, tablefmt="fancy_grid"))
        print(f"\nBatch Accuracy: {batch_acc:.2%}\n")

    return accs


def get_non_null_lines(
    response_path,
    grammar_path,
):
    parses = []
    for i in range(0, 6):
        varfree_path = create_out_path(
            f"output/varfree_lf/{i + 1}/",
            response_path,
            check_exists=False,
            ext=".txt"
        )

        with open(varfree_path, "r") as f:
            lines = [line.strip() for line in f.readlines()]

        bools = np.array([line != "<null>" for line in lines], dtype=bool)
        parses.append(bools)

    return np.stack(parses)


def get_non_rep_lines(response_path, non_null_lines):
    en_lines = []
    ignore_list = DET + AUX + BY + INF + REL_PRON + PP_LOC
    n_repetitions = 0

    for i in range(0, 6):
        sent_path = create_out_path(
            f"output/english/{i + 1}/",
            response_path,
            check_exists=False,
            ext=".txt"
        )

        with open(sent_path, "r") as f:
            en_lines = [
                line for line in f.readlines()
                if line.strip() and not line.startswith("//")
            ]

        for j, line in enumerate(en_lines):
            words = list(set(line.strip().split(" ")))
            reps_list = [
                w for w in words
                if w not in ignore_list and line.count(w) > 1
            ]

            if reps_list:
                n_repetitions += 1
                non_null_lines[i, j] = False

    return non_null_lines


def get_consistent_lines(response_path, non_null_lines):
    valid_lines = non_null_lines
    valid_batches = non_null_lines.all(axis=0)
    vf_lines = []

    for i in range(0, 6):
        varfree_path = create_out_path(
            f"output/varfree_lf/{i + 1}/",
            response_path,
            check_exists=False,
            ext=".txt"
        )

        with open(varfree_path, "r") as f:
            vf_lines_cur = np.array(f.readlines(), dtype=object)
        vf_lines.append(vf_lines_cur[valid_batches])

    vf_lines = np.array(vf_lines, dtype=object).T.tolist()

    pattern = re.compile(r'^(\w+)\s*\(\s*agent\s*=\s*\*?\s*(\w+)', re.M)

    for i, batch in enumerate(vf_lines, start=1):
        verbs, agents = [], []
        for line in batch:
            m = pattern.match(line.strip())
            if m:
                verbs.append(m.group(1))
                agents.append(m.group(2))

        main_verb = verbs[0] if verbs else None
        main_agent = agents[0] if agents else None

        for j, (v, a) in enumerate(zip(verbs, agents)):
            if v != main_verb or a != main_agent:
                print(
                    f"Batch {i+1}, sentence {j+1}: "
                    f"Verb/agent mismatch (verb='{v}', agent='{a}')"
                )
                valid_lines[j, i] = False

    return valid_lines


def main():
    parser = argparse.ArgumentParser(
        description="Execute data generation pipeline"
    )

    parser.add_argument(
        "response_path",
        type=str,
        help="Path to the unformatted response"
    )
    parser.add_argument(
        "grammar_path",
        type=str,
        help="Path to the IRTG grammar file"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    response_path = args.response_path
    grammar_path = args.grammar_path
    verbose = args.verbose

    lines_non_null = get_non_null_lines(response_path, grammar_path)
    print("Parse accuracies")
    accs = get_accuracies(lines_non_null, verbose=verbose)

    lines_consistent = get_consistent_lines(response_path, lines_non_null)
    print("Sentences w/ consistent main S/V")
    accs_cons = get_accuracies(lines_consistent, verbose=verbose)

    lines_non_rep = get_non_rep_lines(response_path, lines_consistent)
    print("Non-repetition sentences")
    accs_rep = get_accuracies(lines_non_rep, verbose=verbose)

    if verbose:
        print(accs)
        print()
        print(accs_cons)
        print()
        print(accs_rep)


if __name__ == "__main__":
    main()
