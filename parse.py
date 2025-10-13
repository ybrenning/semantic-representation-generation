import argparse
import subprocess
from utils import read_grammar, en_header, create_out_path


rel_prons = ["which", "who", "whom"]

grammars = [
    "grammars/g1.irtg",
    "grammars/g2.irtg",
    "grammars/g3.irtg",
    "grammars/g4.irtg",
    "grammars/g5.irtg",
    "grammars/g6.irtg"
]


def format_sents(response_path, verbose=False):
    """
    From the raw GPT-5 output saved in the `responses` directory,
    write a file into the `english` directory that contains the
    sentences in an Alto-parseable format like this:


    // IRTG unannotated corpus file, v1.0
    //
    // interpretation english: de.up.ling.irtg.algebra.StringAlgebra


    the researcher touched the journalist
    the captain accused the lawyer
    the farmer hugged a dog
    the queen saved a patient
    """
    with open(response_path, "r") as f:
        lines = f.readlines()

    sent_types = [en_header for _ in range(6)]
    for line in lines:
        if not line[0].isdigit():
            continue
        assert 1 <= (n := int(line[0])) <= 6

        sent = line[3:]
        sent = sent[0].lower() + sent[1:]
        sent = " ".join([
            w if w not in rel_prons else "that"
            for w in sent.split(" ")
        ])
        sent = sent.replace(" an ", " the ")

        if n == 1:
            batch_det = sent.split(" ")[0]

        sent = batch_det + " " + " ".join(sent.split(" ")[1:])
        sent = sent.replace(",", "")
        sent = sent.strip()
        sent = sent.rstrip(".")
        sent_types[n - 1] += sent + "\n"

    for i, content in enumerate(sent_types):
        sent_path = create_out_path(
            f"output/english/{i + 1}/",
            response_path,
            check_exists=False,
            ext=".txt"
        )
        with open(sent_path, "w") as f:
            f.write(content)
            if verbose:
                print("Saved formatted sentences to", sent_path)


def lexical_parse(sent_path, lex, show_oov=False):
    """
    Given on a file containing English sentences, find and count
    any OOV words and sentencens based on a given lexicon.
    """
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

    if show_oov:
        print()

    return oov_count, oov_sents, sent_count, words


def parse_sents(response_path, base_grammar_path, verbose=False):
    """
    The main parse function takes the response name as well as the
    "base" grammar (i.e., the main grammar used within the prompt).

    It then goes through every sentence type (1)-(6) and uses the
    corresponding semantics grammar to produce semantic representations
    in the `varfree` logical form.

    These parse results can then be used in the evaluation step.
    If the parse is not valid, the corresponding line contains <null>, which
    we use to filter which sentence batches to keep as well as to compute
    an accuracy score. In addition, this function performs a lexical parse
    on each sentence file in order to evaluate OOV percentages.
    """
    oov_count = 0
    oov_sents = 0
    sent_count = 0
    words = set()

    if base_grammar_path.endswith(".irtg"):
        grammar_path = base_grammar_path.replace(".irtg", ".ebnf")

    # Use the base grammar as lexicon
    lex = read_grammar(grammar_path, lex_only=True)

    for i in range(0, 6):
        sent_path = create_out_path(
            f"output/english/{i + 1}/",
            response_path,
            check_exists=False,
            ext=".txt"
        )

        (
            oov_count_cur,
            oov_sents_cur,
            sent_count_cur,
            words_cur
        ) = lexical_parse(
            sent_path,
            lex,
            show_oov=verbose
        )

        oov_count += oov_count_cur
        oov_sents += oov_sents_cur
        sent_count += sent_count_cur
        words.update(words_cur)

        # Use the separate sentence grammars to parse
        sent_grammar_path = grammars[i % 6]

        varfree_path = sent_path.replace("english", "varfree_lf")
        command = (
            "java -cp ../alto/build/libs/alto-2.3.8-SNAPSHOT-all.jar "
            "de.up.ling.irtg.script.ParsingEvaluator "
            f"-g {sent_grammar_path} "
            "-I english -O semantics=cogs "
            f"-o {varfree_path} "
            "--no-derivations "
            f"{sent_path}"
        )

        if verbose:
            subprocess.run(command, shell=True)
            print()
        else:
            subprocess.run(
                command, shell=True, capture_output=True, text=True
            )

    oov_pct_total = oov_count / len(words)
    oov_pct_sent = oov_sents / sent_count

    if verbose:
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


def main():
    parser = argparse.ArgumentParser(
        description="Execute data generation pipeline"
    )

    parser.add_argument(
        "response_path",
        type=str,
        help="Path to the unformatted response"
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

    response_path = args.response_path
    grammar_path = args.grammar_path
    verbose = args.verbose

    format_sents(response_path, verbose=verbose)
    parse_sents(response_path, grammar_path, verbose=verbose)


if __name__ == "__main__":
    main()
