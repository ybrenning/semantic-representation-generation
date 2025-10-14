import sys


def main():

    in_file = sys.argv[1]
    assert in_file.endswith(".irtg")
    out_file = in_file.split(".")[0] + ".ebnf"

    with open(in_file, "r") as f:
        rules_dict = {}
        lines = f.readlines()

    for i, line in enumerate(lines):
        if "->" in line:
            rules = line.strip().split("->")
            lhs, rhs = rules[0], rules[1]
            lhs = lhs.strip()
            if "(" not in rhs:  # Terminal
                rhs = [lines[i+1].split(" ")[-1]]
            else:  # Non-terminal
                # rhs = rhs.split("}")[-1]
                _, midright = rhs.split("(")
                rhs, _ = midright.split(")")

                lhs = lhs.replace("!", "") if lhs == "S!" else lhs
                rhs = rhs.strip().split(",")

            rhs = [r.strip().replace("!", "") for r in rhs]

            if lhs not in rules_dict:
                rules_dict[lhs] = [rhs]
            else:
                rules_dict[lhs].append(rhs)

    output = ""
    for lhs, rhs in rules_dict.items():
        output += lhs + " : "
        rhs = [" ".join(r) for r in rhs]
        output += " | ".join(rhs) + "\n\n"

    with open(out_file, "w") as f:
        f.write(output)


if __name__ == "__main__":
    main()
