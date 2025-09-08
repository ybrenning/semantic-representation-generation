import subprocess

grammar_prefix = "in_distribution"
grammar_path_irtg = "grammars/preprocessed-RC_modifying_subject_NP_gen-grammar.irtg"
grammar_path_ebnf = "grammars/preprocessed-RC_modifying_subject_NP_gen-grammar.ebnf"
in_path = "data/english/in_distribution-english.txt"
in_path = "data/english/prompt-english.txt"

# with open(in_path, "r+") as f:
#     lines = f.readlines()
#     if not lines[0].startswith("//"):
#
#         lines = [
#             " ".join([s.split()[0].lower()] + s.split()[1:-1])
#             for s in lines if s != "\n"
#         ]
#
#         header = """
#         // IRTG unannotated corpus file, v1.0
#         //
#         // interpretation english: de.up.ling.irtg.algebra.StringAlgebra
#
#
#         """
#
#         content = header + "\n".join(lines) + "\n"
#         f.write(content)

out_path = f"data/varfree_lf/{grammar_prefix}-varfree.txt"
out_path = f"data/varfree_lf/prompt-varfree.txt"

from utils import read_grammar

lex = read_grammar(grammar_path_ebnf, lex_only=True)
with open(in_path, "r") as f:
    for line in f.readlines():
        if not line.startswith("//"):
            for word in line.split(" "):
                if word != "\n" and word.strip() not in lex:
                    print(f"Word {word} not in lexicon")


command = (
    "java -cp ../alto/build/libs/alto-2.3.8-SNAPSHOT-all.jar "
    "de.up.ling.irtg.script.ParsingEvaluator "
    f"-g {grammar_path_irtg} "
    "-I english -O semantics=cogs "
    f"-o {out_path} "
    "--no-derivations "
    f"{in_path}"
)

subprocess.run(command, shell=True)

print("Saved representations in variable-free format to", out_path)
