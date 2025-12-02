
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
                    f"r{{{{ cnt.next() }}}} (Det, N_{prep}) [0.0]"
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


def generate_rec_cp_rules(n):
    assert n >= 2, "Recursion depth must be greater than or equal to two"

    grammar_path = f"grammars/slog-rec_cp_{n}.irtg"

    out = """
S! -> r{{ cnt.next() }}(NP_animate_nsubj, VP_CP_0) [0.0]
[english] *(?1, ?2)
[semantics] pre_agent(?2, ?1)
    """

    # Generate VP_CP_i and S_i for i = 0 .. n-2
    for i in range(0, n - 1):
        out += f"""
VP_CP_{i} -> S_embedded_cp_E{{{{ cnt.next() }}}}(V_cp_taking, C, S_{i}) [0.0]
[english] *(?1, *(?2, ?3))
[semantics] ccomp(?1, ?3)

S_{i} -> r{{{{ cnt.next() }}}}(NP_animate_nsubj, VP_CP_{i+1}) [0.0]
[english] *(?1, ?2)
[semantics] pre_agent(?2, ?1)
        """

    out += f"""
VP_CP_{n-1} -> S_embedded_cp_E{{{{ cnt.next() }}}}(V_cp_taking, C, S_{n-1}) [0.0]
[english] *(?1, *(?2, ?3))
[semantics] ccomp(?1, ?3)

S_{n-1} -> r{{{{ cnt.next() }}}}(NP_animate_nsubj, VP_external) [0.0]
[english] *(?1, ?2)
[semantics] pre_agent(?2, ?1)
    """

    base_grammar = """
VP_external -> r{{ cnt.next() }}(V_unerg) [0.125]
[english] ?1
[semantics] ?1

VP_external -> r{{ cnt.next() }}(V_unacc, NP_dobj) [0.125]
[english] *(?1, ?2)
[semantics] theme(?1, ?2)

VP_external -> r{{ cnt.next() }}(V_trans_omissible) [0.125]
[english] ?1
[semantics] ?1

VP_external -> r{{ cnt.next() }}(V_trans_omissible, NP_dobj) [0.125]
[english] *(?1, ?2)
[semantics] theme(?1, ?2)

VP_external -> r{{ cnt.next() }}(V_trans_not_omissible, NP_dobj) [0.125] 
[english] *(?1, ?2)
[semantics] theme(?1, ?2)

VP_external -> r{{ cnt.next() }}(V_inf_taking, INF, V_inf)[0.125]
[english] *(?1, *(?2, ?3))
[semantics] xcomp(?1, ?3)

VP_external -> r{{ cnt.next() }}(V_dat, NP_inanimate_dobj, PP_iobj) [0.125] 
[english] *(*(?1, ?2), ?3)
[semantics] recipient(theme(?1, ?2), ?3)

VP_external -> r{{ cnt.next() }}(V_dat, NP_animate_iobj, NP_inanimate_dobj) [0.125] 
[english] *(*(?1, ?2), ?3)
[semantics] theme(recipient(?1, ?2), ?3)

PP_iobj -> r{{ cnt.next() }} (P_iobj,NP_animate_iobj)[1]
[english] *(?1, ?2)
[semantics] pre_case(?2, ?1)

NP_dobj -> r{{ cnt.next() }}(NP_inanimate_dobj) [0.5]
[english] ?1
[semantics] ?1

NP_dobj -> r{{ cnt.next() }}(NP_animate_dobj) [0.5]
[english] ?1
[semantics] ?1

NP_animate_nsubj -> r{{ cnt.next() }}(Det, N_common_animate_nsubj) [0.5]
[english] *(?1, ?2)
[semantics] pre_det(?2, ?1)

NP_inanimate_dobj -> r{{ cnt.next() }}(Det, N_common_inanimate_dobj) [0.5]
[english] *(?1, ?2)
[semantics] pre_det(?2, ?1)

NP_animate_dobj -> r{{ cnt.next() }}(Det, N_common_animate_dobj) [0.25]
[english] *(?1, ?2)
[semantics] pre_det(?2, ?1)
    """

    with open(grammar_path, "w") as f:
        f.write(out + base_grammar)
        print("Saved grammar to", grammar_path)
