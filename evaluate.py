grammar_prefix = "in_distribution"
out_path = f"data/varfree_lf/{grammar_prefix}-varfree.txt"

with open(out_path, "r") as f:
    correct = 0
    total = 0
    for line in f.readlines():
        if line != "<null>":
            correct += 1
        total += 1

acc = round(correct/total * 100, 2)
print(f"{correct}/{total} ({acc}%) sentences have a valid parse")
