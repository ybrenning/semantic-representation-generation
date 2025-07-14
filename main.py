def main():

    with open("preprocessed-main.irtg", "r") as f:
        rules_dict = {}
        lines = f.readlines()

    for i, line in enumerate(lines):
        if "->" in line:
            rules = line.strip().split("->")
            lhs, rhs = rules[0], rules[1]
            if "(" not in rhs:  # Terminal
                rhs = [lines[i+1].split(" ")[-1]]
            else:  # Non-terminal
                # rhs = rhs.split("}")[-1]
                _, midright = rhs.split("(")
                rhs, _ = midright.split(")")

                lhs = lhs.strip()
                lhs = lhs.replace("!", "") if lhs == "S!" else lhs
                rhs = rhs.strip().split(",")

            rhs = [r.strip() for r in rhs]

            if lhs not in rules_dict:
                rules_dict[lhs] = [rhs]
            else:
                rules_dict[lhs].append(rhs)

    output = ""
    for lhs, rhs in rules_dict.items():
        output += lhs + " : "
        rhs = [" ".join(r) for r in rhs]
        output += " | ".join(rhs) + "\n\n"

    print(output)


if __name__ == "__main__":
    main()
