import re


def clean_line(line):
    # Normalize spaces and remove rule probability
    cleaned = re.sub(r"\s*->\s*", " -> ", line.strip())
    cleaned = re.sub(r"\s*\[[^\]]+\]$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Normalize comma spacing inside parentheses
    def normalize_commas(match):
        inside = match.group(1)
        inside = re.sub(r"\s*,\s*", ", ", inside)
        return f"({inside})"

    cleaned = re.sub(r"\(([^()]*)\)", normalize_commas, cleaned)
    return cleaned


grammars = [
    # "base/main-grammar.irtg",
    # "base/RC_modifying_dobj_NP_main-grammar.irtg",
    # "base/RC_modifying_subject_NP_gen-grammar.irtg"
    "g1.irtg",
    "g2.irtg",
    "g3.irtg",
    "g4.irtg",
    "g5.irtg",
    "g6.irtg"
]

out_file = "combined-grammars-6.irtg"

header = """


interpretation english: de.up.ling.irtg.algebra.StringAlgebra
interpretation semantics: de.saar.coli.algebra.OrderedFeatureTreeAlgebra
















"""
seen = set()
with open(out_file, "w") as f_out:
    f_out.write(header)
    for grammar in grammars:
        with open(grammar, "r") as f_in:
            skip_count = 0
            for line in f_in:
                if skip_count > 0:
                    skip_count -= 1
                    continue

                if "->" in line:
                    cleaned = clean_line(line)
                    if cleaned not in seen:
                        f_out.write(cleaned + "\n")
                        seen.add(cleaned)
                    else:
                        skip_count = 2
                elif line.startswith("interpretation"):
                    continue
                else:
                    f_out.write(line)
        f_out.write("\n")
