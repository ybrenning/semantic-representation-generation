import pandas as pd
import varfree2cogs


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
    sent_file = "data/english/prompt-newest-response-36.txt"
    varfree_file = "data/varfree_lf/prompt-newest-response-36.txt"

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
    ...


if __name__ == "__main__":
    main()
