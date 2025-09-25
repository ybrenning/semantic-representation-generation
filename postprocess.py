import sys
import pandas as pd
import varfree2cogs

from utils import en_header

DET = ["the", "a"]
AUX = ["was"]
BY = ["by"]
INF = ["to"]
REL_PRON = ["that"]
PP_LOC = ["on", "in", "beside"]


def handle_null_sents(sent_path, varfree_path):
    """
    Handle sentences that have <null> parses.

    Note:
        Default for now is probably just to discard them
    """
    with open(sent_path, "r") as f:
        en_lines = []
        for line in f.readlines():
            if line.strip() and not line.startswith("//"):
                en_lines.append(line)

    with open(varfree_path, "r") as f:
        vf_lines = f.readlines()

    assert len(en_lines) == len(vf_lines), "File length mismatch"
    assert len(en_lines) % 6 == 0, "File must contain 6-sentence batches"

    zipped = zip(en_lines, vf_lines)
    for i, pair in enumerate(zipped):
        _, vf = pair
        if vf.strip() == "<null>":
            rel_i = i % 6
            batch_start = i - rel_i
            batch_end = i + (6 - rel_i)
            del en_lines[batch_start:batch_end]
            del vf_lines[batch_start:batch_end]

    return en_lines, vf_lines


def handle_incorrect_sents(en_lines, vf_lines):
    """
    Handle sentences that have a valid parse, but do not
    follow the desired constraints in some way.

    This may include:
        - inconsistent verb/subj/obj within batch
        - incorrect application of grammar rules

    The former can be implemented by a simple check of the semantic
    representations for each batch, the latter must be checked by
    creating a separate, minimal grammar for each sentence type (1..6)

    Either discard them or select some random replacement word from the vocab
    """
    return en_lines, vf_lines


def handle_repetition_sents(en_lines, vf_lines):
    """
    Handle sentences that have some repetition of verb, subject or object.

    Example of such a model output:

    `the king that the king that the king respected adored adored the queen`
    """
    assert len(en_lines) == len(vf_lines), "File length mismatch"
    assert len(en_lines) % 6 == 0, "File must contain 6-sentence batches"
    ignore_list = DET + AUX + BY + INF + REL_PRON + PP_LOC

    for i, pair in enumerate(zip(en_lines, vf_lines)):
        en, vf = pair
        words = list(set(en.strip().split(" ")))
        for w in words:
            if w not in ignore_list and en.count(w) > 1:
                rel_i = i % 6
                batch_start = i - rel_i
                batch_end = i + (6 - rel_i)
                del en_lines[batch_start:batch_end]
                del vf_lines[batch_start:batch_end]

    return en_lines, vf_lines


# only for long distance movement
def move_wh_words(row):
    tokens_list = row.split()
    if tokens_list[0] not in ["Who", "What"]:
        if "Who" in tokens_list:
            who_index = tokens_list.index("Who")
            tokens_list.pop(who_index)
            tokens_list.insert(0, "Who")
            return " ".join(tokens_list)

        if "What" in tokens_list:
            what_index = tokens_list.index("What")
            tokens_list.pop(what_index)
            tokens_list.insert(0, "What")
            return " ".join(tokens_list)

    return row


def postprocess_varfree():
    save_output = True

    grammar_prefix = "in_distribution"

    sent_file = f"data/english/{grammar_prefix}-english.txt"
    varfree_file = f"data/varfree_lf/{grammar_prefix}-varfree.txt"

    with open(sent_file, "r", encoding="utf-8") as f1:
        col1 = [
            line.strip() for line in f1
            if not line.startswith("//")
            and line != "\n"
        ]

    with open(varfree_file, "r", encoding="utf-8") as f2:
        col2 = [line.strip() for line in f2]

    df_alto = pd.DataFrame({
        "source": col1,
        "varfree_lf": col2
    })

    df_alto["types"] = grammar_prefix

    # if wh-questions
    if "wh_" in grammar_prefix:
        # Move the wh-word to the front of the sentence
        # (for long distance movement case)
        df_alto["source"] = df_alto["source"].apply(move_wh_words)

        # Convert varfree LF to COGS LF
        df_alto["cogs_lf"] = df_alto.apply(
            lambda x: varfree2cogs.varfree_to_cogs_lf(
                x.source, x.varfree_lf
            ),
            axis=1
        )

        # add ? to the end of each sentence
        df_alto["source"] = df_alto["source"] + " ?"

        # Replace all occurrences of wh-words with "?" in the LFs
        for target in ["varfree_lf", "cogs_lf"]:
            df_alto[target] = df_alto[target].str.replace("Who", "?")
            df_alto[target] = df_alto[target].str.replace("What", "?")
    else:
        # capitalize the first word of each sentence
        df_alto.source = [
            " ".join([s.split()[0].capitalize()] + s.split()[1:])
            for s in df_alto.source
        ]

        # add . to the end of each sentence
        df_alto["source"] = df_alto["source"] + " ."

        df_alto["cogs_lf"] = df_alto.apply(
            lambda x: varfree2cogs.varfree_to_cogs_lf(
                x.source, x.varfree_lf
            ),
            axis=1
        )

    if save_output:
        df_alto[["source", "cogs_lf", "types"]].to_csv(
            "data/cogs_lf/cogs_" + grammar_prefix + ".tsv",
            sep='\t', index=False, header=False
        )
        df_alto[["source", "varfree_lf", "types"]].to_csv(
            "data/varfree_lf/varfree_" + grammar_prefix + ".tsv",
            sep='\t', index=False, header=False
        )
    else:
        print(df_alto[["source", "varfree_lf", "types"]])
        print("")
        print(df_alto[["source", "cogs_lf", "types"]])


def main():
    sent_path = sys.argv[1]
    varfree_path = "output/varfree_lf/" + sent_path.split("/")[-1]

    en_lines, vf_lines = handle_null_sents(sent_path, varfree_path)
    en_lines, vf_lines = handle_incorrect_sents(en_lines, vf_lines)
    en_lines, vf_lines = handle_repetition_sents(en_lines, vf_lines)

    sent_path_out = "data/english/" + sent_path.split("/")[-1]
    varfree_path_out = "data/varfree_lf/" + sent_path.split("/")[-1]

    with open(sent_path_out, "w") as f:
        f.write(en_header + "".join(en_lines))

    with open(varfree_path_out, "w") as f:
        f.write("".join(vf_lines))


if __name__ == "__main__":
    main()
