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
                sent = sent[0].lower() + sent[1:]
                sent = " ".join([
                    w if w not in rel_prons else "that"
                    for w in sent.split(" ")
                ])
                sent = sent.replace(" an ", " the ")

                if i == 0:
                    batch_det = sent.split(" ")[0]

                sent = batch_det + " " + " ".join(sent.split(" ")[1:])
                sent = sent.replace(",", "")
                sent = sent.strip()
                sent = sent.rstrip(".")
                content += sent + "\n"

                i += 1
                if i == 6:
                    i = 0

    out_file = "data/english/" + response_path.split("/")[-1]
    with open(out_file, "w") as f:
        f.write(content)

    return out_file


def lexical_parse(sent_path, grammar_path, show_stats=False, show_oov=False):
    if grammar_path.endswith(".irtg"):
        grammar_path = grammar_path.replace(".irtg", ".ebnf")

    lex = read_grammar(grammar_path, lex_only=True)
    words = set()
    sent_count = 0
    oov_count = 0
    oov_sents = 0
    with open(sent_path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue

            sent_count += 1
            oov_current_sent = 0
            for word in line.split(" "):
                word = word.strip()
                if not word:
                    continue

                if show_oov and word not in lex:
                    print(f"Word \"{word}\" not in lexicon")
                    oov_current_sent += 1
                elif word not in words and word not in lex:
                    oov_current_sent += 1
                words.add(word)

            oov_count += oov_current_sent
            oov_sents += 1 if oov_current_sent != 0 else oov_current_sent

    oov_pct_total = oov_count / len(words)
    oov_pct_sent = oov_sents / sent_count

    if show_stats:
        print("-----------")
        print(
            f"Total OOV percentage: "
            f"{oov_count} / {len(words)} = "
            f"{oov_pct_total:.2%}"
        )
        print(
            f"OOV sentences: "
            f"{oov_sents} / {sent_count} = "
            f"{oov_pct_sent:.2%}"
        )
        print("-----------")

    return oov_pct_total, oov_pct_sent


def parse_sents(sent_path, grammar_path):
    if grammar_path.endswith(".irtg"):
        grammar_path_irtg = grammar_path
        grammar_path_ebnf = grammar_path.replace(".irtg", ".ebnf")

    lexical_parse(
        sent_path,
        grammar_path_ebnf,
        show_oov=True
    )

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
