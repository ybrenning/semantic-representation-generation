import json
import numpy as np
import sys
from parse import lexical_parse


def get_parse_accuracies(lines, show_stats=True):
    accuracies = {}
    batch_size = 6

    total_lines = 0
    correct_lines = 0

    total_batches = 0
    not_null_batches = 0
    correct_batches = 0
    line_position_correct = [0] * batch_size
    line_position_total = [0] * batch_size

    for i in range(0, len(lines), batch_size):
        batch = lines[i:i+batch_size]
        if len(batch) < batch_size:
            continue

        for j, line in enumerate(batch):
            total_lines += 1
            line_position_total[j] += 1
            if line.strip() != "<null>":
                correct_lines += 1
                line_position_correct[j] += 1

        total_batches += 1
        if all(line.strip() != "<null>" for line in batch):
            not_null_batches += 1

        main_verb = batch[0].split("(")[0]
        if all(line.strip().startswith(main_verb) for line in batch):
            correct_batches += 1

    if show_stats:
        print(
            f"Line parse accuracy: "
            f"{correct_lines}/{total_lines} = "
            f"{correct_lines / total_lines:.2%}"
        )
        print(
            f"Batch parse accuracy: "
            f"{not_null_batches}/{total_batches} = "
            f"{not_null_batches / total_batches:.2%}"
        )
        print(
            f"Batch form accuracy: "
            f"{correct_batches}/{total_batches} = "
            f"{correct_batches / total_batches:.2%}"
        )

        accuracies["line_acc"] = round(correct_lines / total_lines, 4)
        accuracies["batch_acc"] = round(not_null_batches / total_batches, 4)
        accuracies["batch_form_acc"] = round(
            correct_batches / total_batches, 4
        )
        accuracies["sent_accs"] = []

        print("-----------")
        print("Accuracy per sentence type:")
        for j in range(batch_size):
            acc = (
                line_position_correct[j] / line_position_total[j]
                if line_position_total[j] > 0 else 0
            )

            accuracies["sent_accs"].append(round(acc, 4))

            print(
                f"  Sentence {j+1}: "
                f"{line_position_correct[j]}/{line_position_total[j]}"
                f"= {acc:.2%}"
            )
        print("-----------")

        return accuracies


def infer_n_prompts(varfree_path):
    parts = varfree_path.split("-")
    for i, part in enumerate(parts):
        if part.startswith("response") and i > 0:
            if parts[i-1].isdigit():
                return int(parts[i-1])
    return 1


def evaluate_parse(
    response_path,
    grammar_path,
    verbose=False,
    save_metrics=True
):

    metrics_path = (
        "output/metrics/" +
        response_path.split("/")[-1].replace(".txt", ".json")
    )

    parses = []
    for i in range(0, 6):
        varfree_path = (
            f"output/varfree_lf/{i + 1}/" + response_path.split("/")[-1]
        )

        with open(varfree_path, "r") as f:
            lines = [line.strip() for line in f.readlines()]

        bools = np.array([line != "<null>" for line in lines], dtype=bool)
        parses.append(bools)
        assert len(lines) % 6 == 0, "File must contain 6-sentence batches"

    assert len(parses) == 6
    parses = np.stack(parses)
    print(parses)

    # Accuracy per sentence type
    sent_accs = parses.mean(axis=1) 
    # Accuracy of batches
    batch_acc = parses.all(axis=0).mean()

    return sent_accs, batch_acc


def main():
    # TODO: make argparse
    response_path = "generation/responses/prompt-newest-10-responses-18.txt"
    base_grammar_path = "grammars/preprocessed-combined.irtg"
    sent_accs, batch_acc = evaluate_parse(response_path, base_grammar_path, verbose=True)
    print(sent_accs, batch_acc)


if __name__ == "__main__":
    main()
