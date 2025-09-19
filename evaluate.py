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
    correct_batches = 0

    # Show vocab-specific information
    lexical_parse(
        sent_path,
        grammar_path,
        show_stats=True,
        show_oov=True
    )

    for i in range(0, len(lines), batch_size):
        batch = lines[i:i+batch_size]
        if len(batch) < batch_size:
            continue

        for line in batch:
            total_lines += 1
            if line.strip() != "<null>":
                correct_lines += 1

        total_batches += 1
        if all(line.strip() != "<null>" for line in batch):
            correct_batches += 1

    print(f"Line accuracy: {correct_lines}/{total_lines} = {correct_lines / total_lines:.2%}")
    print(f"Batch accuracy: {correct_batches}/{total_batches} = {correct_batches / total_batches:.2%}")


def main():
    varfree_path = sys.argv[1]
    grammar_path = sys.argv[2]
    assert varfree_path.endswith(".txt")
    get_parse_accuracy(varfree_path, grammar_path)


if __name__ == "__main__":
    main()
