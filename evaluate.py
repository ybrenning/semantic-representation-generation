import numpy as np
from tabulate import tabulate


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
        print(f"\nBatch Accuracy: {batch_acc:.2%}")

    return accs


def get_non_null_lines(
    response_path,
    grammar_path,
):
    parses = []
    for i in range(0, 6):
        varfree_path = (
            f"output/varfree_lf/{i + 1}/" + response_path.split("/")[-1]
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
        sent_path = (
            f"output/english/{i + 1}/" + response_path.split("/")[-1]
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


def main():
    # TODO: make argparse
    response_path = "generation/responses/prompt-newest-5-responses-2.txt"
    base_grammar_path = "grammars/preprocessed-combined.irtg"
    lines_b = get_non_null_lines(
        response_path, base_grammar_path
    )
    print(lines_b)
    lines = get_non_rep_lines(response_path, lines_b)
    print(lines)


if __name__ == "__main__":
    main()
