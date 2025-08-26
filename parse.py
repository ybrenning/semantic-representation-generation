import subprocess

grammar_prefix = "in_distribution"
grammar_path = "grammars/preprocessed-main.irtg"
in_path = "data/english/in_distribution-english.txt"
in_path = "data/english/prompt-english.txt"

with open(in_path, "r+") as f:
    lines = f.readlines()
    if not lines[0].startswith("//"):

        lines = [
            " ".join([s.split()[0].lower()] + s.split()[1:-1])
            for s in lines if s != "\n"
        ]

        header = """
        // IRTG unannotated corpus file, v1.0
        //
        // interpretation english: de.up.ling.irtg.algebra.StringAlgebra


        """

        content = header + "\n".join(lines) + "\n"
        f.write(content)

out_path = f"data/varfree_lf/{grammar_prefix}-varfree.txt"
out_path = f"data/varfree_lf/prompt-varfree.txt"

command = (
    "java -cp ../alto/build/libs/alto-2.3.8-SNAPSHOT-all.jar "
    "de.up.ling.irtg.script.ParsingEvaluator "
    f"-g {grammar_path} "
    "-I english -O semantics=cogs "
    f"-o {out_path} "
    "--no-derivations "
    f"{in_path}"
)

subprocess.run(command, shell=True)

print("Saved representations in variable-free format to", out_path)
