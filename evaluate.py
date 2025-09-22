import sys
from parse import lexical_parse


def get_parse_accuracy(varfree_path, grammar_path):
    sent_path = "data/english/" + varfree_path.split("/")[-1]

    with open(varfree_path, "r") as f:
        lines = f.readlines()

    batch_size = 6

    total_lines = 0
    correct_lines = 0

    total_batches = 0
    not_null_batches = 0
    correct_batches = 0

    # Show vocab-specific information
    lexical_parse(
        sent_path,
        grammar_path,
        show_stats=True,
        show_oov=True
    )

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

    print(f"Line parse accuracy: {correct_lines}/{total_lines} = {correct_lines / total_lines:.2%}")
    print(f"Batch parse accuracy: {not_null_batches}/{total_batches} = {not_null_batches / total_batches:.2%}")
    print(f"Batch form accuracy: {correct_batches}/{total_batches} = {correct_batches / total_batches:.2%}")

    print("-----------")
    print("\nAccuracy per sentence type:")
    for j in range(batch_size):
        acc = line_position_correct[j] / line_position_total[j] if line_position_total[j] > 0 else 0
        print(f"  Sentence {j+1}: {line_position_correct[j]}/{line_position_total[j]} = {acc:.2%}")
    print("-----------")


def main():
    varfree_path = sys.argv[1]
    grammar_path = sys.argv[2]
    assert varfree_path.endswith(".txt")
    get_parse_accuracy(varfree_path, grammar_path)


if __name__ == "__main__":
    main()
