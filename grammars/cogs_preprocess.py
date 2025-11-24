import argparse
import numpy as np
from scipy.stats import zipf
from jinja2 import Environment, FileSystemLoader


def align_rules_with_tabs(input_text):
    lines = input_text.splitlines()
    updated_lines = []

    for line in lines:
        if "->" in line:
            fst, snd = line.split("[")
            new_line = fst + "\t" + "[" + snd
            updated_lines.append(new_line)
        elif line.startswith("["):
            new_line = "  " + line
            updated_lines.append(new_line)
        else:
            updated_lines.append(line)

    return "\n".join(updated_lines)


class _Counter(object):
    def __init__(self, start_value=1):
        self.value = start_value

    def current(self):
        return self.value

    def next(self):
        v = self.value
        self.value += 1
        return v


# Assign Zipfian distribution to vocab
def normalize(probs):
    # AK: Why is this not simply probs/sum(probs)?
    # The code below does not maintain the ratios between
    # the different probabilities.
    leftover_prob = 1-sum(probs)
    probs = probs + leftover_prob/len(probs)
    return probs


def generate_vocab_probabilities(words):
    a = 1.4
    probs = zipf.pmf(np.array(range(1, len(words)+1)), a)
    probs = normalize(probs)
    return zip(words, probs)


def main():
    parser = argparse.ArgumentParser(
        description="Execute data generation pipeline"
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
    grammar_path = args.grammar_path
    verbose = args.verbose

    # Process the templates
    env = Environment(loader=FileSystemLoader("."))
    env.globals["counter"] = _Counter
    env.filters["zipf"] = generate_vocab_probabilities

    template = env.get_template("specify_grammar.irtg")
    temp_str = template.render(
        grammar_path=grammar_path
    )

    aligned_string = align_rules_with_tabs(temp_str)
    if verbose:
        print(aligned_string)

    grammar_path = "preprocessed-" + grammar_path
    with open(grammar_path, "w") as f:
        f.write(aligned_string)
        print("Saved preprocessed grammar to", grammar_path)


if __name__ == "__main__":
    main()
