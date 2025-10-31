import os


en_header = """
// IRTG unannotated corpus file, v1.0
//
// interpretation english: de.up.ling.irtg.algebra.StringAlgebra


"""


def create_out_path(base_dir, response_path, check_exists, ext):
    filename = os.path.basename(response_path)
    base, _ = os.path.splitext(filename)
    filename = base + ext
    output_path = os.path.join(base_dir, filename)

    if check_exists and os.path.exists(output_path):
        raise FileExistsError(f"Output file already exists: {output_path}")

    return output_path


def read_grammar(grammar_path, lex_only=False):
    grammar = {}
    with open(grammar_path, "r") as f:
        for line in f:
            if lex_only and line.startswith("S :"):
                break

            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" not in line:
                raise ValueError(f"Invalid grammar line (missing ':'): {line}")

            lhs, rhs = line.split(":", 1)
            lhs = lhs.strip()
            alternatives = [r.strip().split() for r in rhs.split("|")]

            grammar[lhs] = alternatives

    if lex_only:
        flattened = [word for sublist in grammar.values() for inner in sublist for word in inner]
        lexicon = set(flattened)
        return lexicon
    else:
        return grammar


def normalize(value):
    """Convert lists to frozensets (recursively if needed) so order doesn't matter."""
    if isinstance(value, list):
        return frozenset(normalize(v) for v in value)
    elif isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    elif isinstance(value, set):
        return frozenset(normalize(v) for v in value)
    return value


def compare_grammars(g1_path, g2_path):

    g1 = read_grammar(g1_path)
    print(g1)
    assert 0
    g2 = read_grammar(g2_path)

    if g1.keys() != g2.keys():
        print("Only in dict1:", g1.keys() - g2.keys())

        # Keys only in dict2
        print("Only in dict2:", g2.keys() - g1.keys())

        different_values = {
            k: (g1[k], g2[k])
            for k in g1.keys() & g2.keys()
            if normalize(g1[k]) != normalize(g2[k])
        }
        print(different_values)

        return False

    return all(set(g1[k]) == set(g2[k]) for k in g1)


def get_safe_filename(filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(new_filename):
        new_filename = f"{base}-{counter}{ext}"
        counter += 1
    return new_filename


def generate_rec_pp_rules(n):
    grammar_path = f"grammars/slog-rec_pp_{n}.irtg"
    base_grammar = """
{## Sentences and verb phrases ##}
S! -> r{{ cnt.next() }}(NP_animate_nsubj, VP_external) [0.9]
[english] *(?1, ?2)
[semantics] pre_agent(?2, ?1)

VP_external -> r{{ cnt.next() }}(V_unacc, NP_dobj) [0.2]
[english] *(?1, ?2)
[semantics] theme(?1, ?2)

VP_external -> r{{ cnt.next() }}(V_trans_omissible, NP_dobj) [0.2]
[english] *(?1, ?2)
[semantics] theme(?1, ?2)

VP_external -> r{{ cnt.next() }}(V_trans_not_omissible, NP_dobj) [0.2] 
[english] *(?1, ?2)
[semantics] theme(?1, ?2)

VP_external -> I_dobj_before_iobj_F{{ cnt.next() }}(V_dat, NP_inanimate_dobj, PP_iobj) [0.2]
[english] *(*(?1, ?2), ?3)
[semantics] recipient(theme(?1, ?2), ?3)

VP_external -> I_dobj_after_iobj_F{{ cnt.next() }}(V_dat, NP_animate_iobj, NP_inanimate_dobj) [0.2]
[english] *(*(?1, ?2), ?3)
[semantics] theme(recipient(?1, ?2), ?3)


{## Noun phrases ##}

NP_dobj -> r{{ cnt.next() }}(NP_inanimate_dobj) [0.5]
[english] ?1
[semantics] ?1

NP_dobj -> r{{ cnt.next() }}(NP_animate_dobj) [0.5]
[english] ?1
[semantics] ?1

NP_animate_dobj -> S_PP_E{{ cnt.next() }}(Det, N_common_animate_dobj, PP_loc_1) [1]
[english] *(*(?1, ?2), ?3)
[semantics] nmod(pre_det(?2, ?1), ?3)

NP_animate_iobj -> r{{ cnt.next() }}(Det, N_common_animate_iobj) [0.5]
[english] *(?1, ?2)
[semantics] pre_det(?2, ?1)

NP_animate_iobj -> r{{ cnt.next() }}(N_prop_iobj) [0.5]
[english] ?1
[semantics] ?1



NP_animate_nsubj -> r{{ cnt.next() }}(Det, N_common_animate_nsubj) [0.5]
[english] *(?1, ?2)
[semantics] pre_det(?2, ?1)

NP_animate_nsubj -> r{{ cnt.next() }}(N_prop_nsubj) [0.5]
[english] ?1
[semantics] ?1

NP_inanimate_dobj -> S_PP_E{{ cnt.next() }}(Det, N_common_inanimate_dobj, PP_loc_1) [1]
[english] *(*(?1, ?2), ?3)
[semantics] nmod(pre_det(?2, ?1), ?3)

PP_iobj -> r{{ cnt.next() }} (P_iobj,NP_animate_iobj)[1]
[english] *(?1, ?2)
[semantics] pre_case(?2, ?1)
    """
    out = []
    for prep in ["on", "in", "beside"]:
        for i in reversed(range(n)):
            out.append(
                f"PP_loc_{i} -> "
                f"r{{{{ cnt.next() }}}} (P_{prep},NP_{prep}_{i}) [0.0]"
            )
            out.append("[english] *(?1, ?2)")
            out.append("[semantics] pre_case(?2, ?1)")

            if i == 0:
                out.append(
                    f"NP_{prep}_{i} -> "
                    "r{{{{ cnt.next() }}}} (Det, N_{prep}) [0.0]"
                )
                out.append("[english] *(?1, ?2)")
                out.append("[semantics] pre_det(?2, ?1)")
            else:
                out.append(
                    f"NP_{prep}_{i} -> "
                    f"S_PP_E{{{{ cnt.next() }}}} "
                    f"(Det, N_{prep}, PP_loc_{i-1}) [0.0]"
                )
                out.append("[english] *(*(?1, ?2), ?3)")
                out.append("[semantics] nmod(pre_det(?2, ?1), ?3)")
            out.append("")

    with open(grammar_path, "w") as f:
        f.write(base_grammar + "\n".join(out))
