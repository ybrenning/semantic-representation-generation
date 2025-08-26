in_file = "prompts/prompt-tree-vocab-response.txt"
with open(in_file, "r") as f:
    content = """
// IRTG unannotated corpus file, v1.0
//
// interpretation english: de.up.ling.irtg.algebra.StringAlgebra


"""

    for line in f.readlines():
        if line[0].isdigit():
            sent = line[3:]
            sent = sent[0].lower() + sent[1:-2]
            content += sent + "\n"

out_file = "data/english/prompt-english.txt"
with open(out_file, "w") as f:
    f.write(content)


