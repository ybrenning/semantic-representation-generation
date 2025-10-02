def clean_line(line):
    # Remove rule probability
    cleaned = re.sub(r"\s*\[[^\]]+\]$", "", line)

    # Normalize comma spacing inside parentheses
    def normalize_commas(match):
        inside = match.group(1)
        # Single space after commas
        inside = re.sub(r"\s*,\s*", ", ", inside)
        return f"({inside})"

    cleaned = re.sub(r"\(([^()]*)\)", normalize_commas, cleaned)

    return cleaned


grammars = [
    "base/main-grammar.irtg",
    "base/RC_modifying_dobj_NP_main-grammar.irtg",
    "base/RC_modifying_subject_NP_gen-grammar.irtg"
]

out_file = "combined-grammars.irtg"

seen = set()
with open(out_file, "w") as f_out:
    for grammar in grammars:
        with open(grammar, "r") as f_in:
            skip_count = 0
            for line in f_in:
                if skip_count > 0:
                    print("skipping subsequent", line)
                    skip_count -= 1
                    continue

                import re
                if "->" in line:
                    cleaned = clean_line(line)
                    if cleaned not in seen:
                        f_out.write(line)
                        seen.add(cleaned)
                    else:
                        print("skipping", line)
                        print(cleaned)
                        skip_count = 2
                else:
                    print("writing", line)
                    f_out.write(line)
        f_out.write("\n")
