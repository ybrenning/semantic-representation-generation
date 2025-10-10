import pandas as pd
import varfree2cogs
from utils import create_out_path


def postprocess_varfree(sent_path, varfree_path, verbose=False):
    with open(sent_path, "r", encoding="utf-8") as f1:
        col1 = [
            line.strip() for line in f1
            if not line.startswith("//")
            and line != "\n"
        ]

    with open(varfree_path, "r", encoding="utf-8") as f2:
        col2 = [line.strip() for line in f2]

    print(col1)
    print(col2)
    df_alto = pd.DataFrame({
        "source": col1,
        "varfree_lf": col2
    })

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

    cogs_path = create_out_path(
        "data/cogs_lf", sent_path, check_exists=True, ext=".tsv"
    )
    df_alto[["source", "cogs_lf"]].to_csv(
        cogs_path,
        sep='\t', index=False, header=False
    )
    print("Saved COGS LF to", cogs_path)

    # df_alto[["source", "varfree_lf", "types"]].to_csv(
    #     "data/varfree_lf/varfree_" + grammar_prefix + ".tsv",
    #     sep='\t', index=False, header=False
    # )

    if verbose:
        print(df_alto[["source", "varfree_lf"]])
        print("")
        print(df_alto[["source", "cogs_lf"]])


def main():
    sent_path = "data/english/prompt-newest-response-22.txt"
    varfree_path = "data/varfree_lf/prompt-newest-response-22.txt"
    postprocess_varfree(sent_path, varfree_path, verbose=True)


if __name__ == "__main__":
    main()
