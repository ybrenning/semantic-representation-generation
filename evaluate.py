import numpy as np


def evaluate_parse(
    response_path,
    grammar_path,
    verbose=False,
):

    from tabulate import tabulate
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

    # Accuracy per sentence type
    sent_accs = parses.mean(axis=1)
    # Accuracy of batches
    batch_acc = parses.all(axis=0).mean()

    accs = {}
    accs["sent_accs"] = sent_accs
    accs["batch_acc"] = batch_acc

    headers = ["Sentence Type", "Accuracy"]
    table = [(f"Type {i+1}", f"{acc:.2%}") for i, acc in enumerate(sent_accs)]
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))
    print(f"\nBatch Accuracy: {batch_acc:.2%}")

    return accs


def main():
    # TODO: make argparse
    response_path = "generation/responses/prompt-newest-10-responses-18.txt"
    base_grammar_path = "grammars/preprocessed-combined.irtg"
    _ = evaluate_parse(
        response_path, base_grammar_path, verbose=True
    )


if __name__ == "__main__":
    main()
