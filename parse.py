import subprocess
import sys
from utils import read_grammar


rel_prons = ["which", "who", "whom"]


def format_sents(response_path):
    with open(response_path, "r") as f:
        content = """
// IRTG unannotated corpus file, v1.0
//
// interpretation english: de.up.ling.irtg.algebra.StringAlgebra


"""

        i = 0
        for line in f.readlines():
            if line[0].isdigit():
                sent = line[3:]
                sent = sent[0].lower() + sent[1:-2]
                sent = " ".join([
                    w if w not in rel_prons else "that"
                    for w in sent.split(" ")
                ])

                if i == 0:
                    batch_det = sent.split(" ")[0]
                elif i == 5:
                    i = 0
                i += 1

                sent = batch_det + " " + " ".join(sent.split(" ")[1:])
                sent = sent.replace(",", "")
                content += sent + "\n"

    out_file = "data/english/" + response_path.split("/")[-1]
    with open(out_file, "w") as f:
        f.write(content)

    return out_file


def parse_sents(sent_path, grammar_path):
    if grammar_path.endswith(".irtg"):
        grammar_path_irtg = grammar_path
        grammar_path_ebnf = grammar_path.replace(".irtg", ".ebnf")

    lex = read_grammar(grammar_path_ebnf, lex_only=True)
    with open(sent_path, "r") as f:
        for line in f.readlines():
            if not line.startswith("//"):
                for word in line.split(" "):
                    if word != "\n" and word.strip() not in lex:
                        print(f"Word {word.strip()} not in lexicon")

    varfree_path = "data/varfree_lf/" + sent_path.split("/")[-1]
    command = (
        "java -cp ../alto/build/libs/alto-2.3.8-SNAPSHOT-all.jar "
        "de.up.ling.irtg.script.ParsingEvaluator "
        f"-g {grammar_path_irtg} "
        "-I english -O semantics=cogs "
        f"-o {varfree_path} "
        "--no-derivations "
        f"{sent_path}"
    )

    subprocess.run(command, shell=True)

    print("Saved representations in variable-free format to", varfree_path)
    return varfree_path


def main():
    sent_path = sys.argv[1]
    grammar_path = sys.argv[2]
    assert sent_path.endswith(".txt")
    assert grammar_path.endswith(".irtg")
    parse_sents(sent_path, grammar_path)


if __name__ == "__main__":
    main()
