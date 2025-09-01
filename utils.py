def read_grammar(grammar_path):
    grammar = {}
    with open(grammar_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" not in line:
                raise ValueError(f"Invalid grammar line (missing ':'): {line}")

            lhs, rhs = line.split(":", 1)
            lhs = lhs.strip()
            alternatives = [r.strip().split() for r in rhs.split("|")]

            grammar[lhs] = alternatives
    return grammar


def normalize(value):
    """Convert lists to frozensets (recursively if needed) so order doesn't matter."""
    if isinstance(value, list):
        return frozenset(normalize(v) for v in value)
    elif isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    elif isinstance(value, set):
        return frozenset(normalize(v) for v in value)
    return value


def compare_grammars(g1_path, g2_path):

    g1 = read_grammar(g1_path)
    g2 = read_grammar(g2_path)

    if g1.keys() != g2.keys():
        print("Only in dict1:", g1.keys() - g2.keys())

        # Keys only in dict2
        print("Only in dict2:", g2.keys() - g1.keys())

        different_values = {
            k: (g1[k], g2[k])
            for k in g1.keys() & g2.keys()
            if normalize(g1[k]) != normalize(g2[k])
        }
        print(different_values)

        return False

    return all(set(g1[k]) == set(g2[k]) for k in g1)


def evaluate(varfree_path):
    with open(varfree_path, "r") as f:
        correct = 0
        total = 0
        for line in f.readlines():
            if line != "<null>\n":
                correct += 1
            total += 1

    acc = round(correct/total * 100, 2)
    print(f"{correct}/{total} ({acc}%) sentences have a valid parse")


varfree_path = "data/varfree_lf/prompt-varfree.txt"
# evaluate(varfree_path)
g1 = "grammars/preprocessed-combined.ebnf"
g2 = "grammars/custom-grammar.ebnf"
print(compare_grammars(g1, g2))
