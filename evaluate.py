import json
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
    varfree_path, grammar_path, show_stats=True, show_oov=True
):
    results = {}

    sent_path = "data/english/" + varfree_path.split("/")[-1]
    results_path = (
        "results/" + varfree_path.split("/")[-1].replace(".txt", ".json")
    )

    with open(varfree_path, "r") as f:
        lines = f.readlines()

    assert len(lines) % 6 == 0, "File must contain 6-sentence batches"

    n_prompts = infer_n_prompts(varfree_path)
    sents_per_prompt = len(lines) / n_prompts
    batches_per_prompt = int(sents_per_prompt / 6)

    results["n_prompts"] = n_prompts
    results["n_batches"] = batches_per_prompt
    results["n_sents"] = len(lines)

    # Show vocab-specific information
    oov_pct_total, oov_pct_sent = lexical_parse(
        sent_path,
        grammar_path,
        show_stats=show_stats,
        show_oov=show_oov
    )

    results["oov"] = {"oov_total": oov_pct_total, "oov_sent": oov_pct_sent}

    results["accuracies"] = get_parse_accuracies(lines)
    with open(results_path, "w") as f:
        json.dump(results, f)
        print("Saved scores to", results_path)


def main():
    varfree_path = sys.argv[1]
    grammar_path = sys.argv[2]
    assert varfree_path.endswith(".txt")

    evaluate_parse(
        varfree_path,
        grammar_path,
        show_stats=True,
        show_oov=True
    )


if __name__ == "__main__":
    main()
