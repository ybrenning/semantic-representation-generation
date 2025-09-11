in_file = "prompts/prompt-tree-vocab-10-response.txt"

rel_prons = ["which", "who", "whom"]

with open(in_file, "r") as f:
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
            content += sent + "\n"

out_file = "data/english/prompt-english-10.txt"
with open(out_file, "w") as f:
    f.write(content)
