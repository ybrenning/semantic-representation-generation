grammars = [
    "main-grammar.irtg",
    "RC_modifying_dobj_NP_main-grammar.irtg",
    "RC_modifying_subject_NP_gen-grammar.irtg"
]

out_file = "combined-grammars.irtg"

seen = set()
with open(out_file, "w") as f_out:
    for grammar in grammars:
        with open(grammar, "r") as f_in:
            skip_count = 0
            for line in f_in:
                if skip_count > 0:
                    print("skipping", line)
                    skip_count -= 1
                    continue

                import re
                if "->" in line:
                    cleaned = re.sub(r"\s*\[[^\]]+\]$", "", line)
                    if cleaned not in seen:
                        f_out.write(line)
                        seen.add(cleaned)
                    else:
                        print("skipping", line)
                        skip_count = 2
                else:
                    f_out.write(line)
