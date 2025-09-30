import random


subsample_terminals = [
    "N_common_animate_dobj ",
    "N_common_animate_iobj ",
    "N_common_animate_nsubj ",
    "N_common_animate_nsubjpass ",

    "N_common_inanimate_dobj ",
    "N_common_inanimate_nsubjpass ",
    "N_common_inanimate_nsubj ",
    "N_prop_dobj ",
    "N_prop_iobj ",
    "N_prop_nsubj ",
    "N_prop_nsubjpass ",
    "N_on ",
    "N_in ",
    "N_beside ",

    "V_trans_omissible ",
    "V_trans_omissible_inf ",
    "V_trans_omissible_pp ",
    "V_trans_not_omissible ",
    "V_trans_not_omissible_inf ",
    "V_trans_not_omissible_pp ",
    "V_cp_taking ",
    "V_cp_taking_inf ",
    "V_inf_taking ",
    "V_unacc ",
    "V_unacc_inf ",
    "V_unacc_pp ",
    "V_unerg ",
    "V_inf ",
    "V_dat ",
    "V_dat_pp ",
    "V_dat_inf ",
]


def prompt_from_grammar(grammar_path, n_sets=3, k=None):
    if grammar_path.endswith(".irtg"):
        grammar_path = grammar_path.replace(".irtg", ".ebnf")

    rules = []
    lexicon = []
    rules_section = False

    with open(grammar_path, "r") as f:
        for line in f:
            if not rules_section and line.startswith("S : "):
                rules_section = True
                rules.append(line)
            elif rules_section:
                rules.append(line)
            else:
                if k and line.startswith(tuple(subsample_terminals)):
                    words = line.split(":")
                    assert len(words) == 2

                    words = [w.strip() for w in words[-1].split("|")]
                    k_curr = max(0, min(k, len(words)))
                    subsample = random.sample(words, k_curr)

                    line_subsampled = (
                        line.split(":")[0]
                        + ": "
                        + " | ".join(subsample) + "\n"
                    )

                    lexicon.append(line_subsampled)
                else:
                    lexicon.append(line)

    rules = "".join(rules)
    lexicon = "".join(lexicon)
    if n_sets > 1:
        constraints = f"""
I would like you to repeat this process in {n_sets} sets of 6 sentences.

Constraints:

- Always use the *same* main subject, main verb and following object throughout the set (6 sentences)
- Make sure the content makes logical sense
- Make sure embedded subjects and verbs within the same sentence are *different* from one another
- Make sure to choose varied terminals from one set to another

So your task is to generate {n_sets} sets of 6 sentences, from a restricted vocabulary, all derived from specific grammar rules. You need to follow the constraints.
        """
    else:
        constraints = f"""
Constraints:

- Always use the *same* main subject, main verb and following object throughout the 6 sentences
- Make sure the content makes logical sense
- Make sure embedded subjects and verbs within the same sentence are *different* from one another

So your task is to generate 6 sentences, from a restricted vocabulary, all derived from specific grammar rules. You need to follow the constraints.
        """

    prompt = f"""
You are an expert linguist. You need to generate 6 sentences based on the following derivations from a context-free grammar:

1.
```
(S
  (NP_animate_nsubj
    (Det)
    (N_common_animate_nsubj)
  )
  (VP_external
    (V_trans_not_omissible)
    (NP_dobj
      (NP_animate_dobj
        (Det)
        (N_common_animate_dobj)
      )
    )
  )
)
```

2.
```
(S
  (NP_animate_nsubj
    (Det)
    (N_common_animate_nsubj)
    (PP_loc)
  )
  (VP_external
    (V_trans_not_omissible)
    (NP_dobj
      (NP_animate_dobj
        (Det)
        (N_common_animate_dobj)
      )
    )
  )
)
```

3.
```
(S
  (NP_animate_nsubj_main_RC_modified
    (NP_animate_nsubj_rec
        (NP_animate_nsubj_main
          (Det)
          (N_common_animate_nsubj)
        )
    )
    (Rel_pron)
    (VP_RC_agent
      (V_unerg)
    )
  )
  (VP_main_anim_subj
    (V_trans_not_omissible)
    (NP_dobj
      (NP_animate_dobj
        (Det)
        (N_common_animate_dobj)
      )
    )
  )
)
```

4.
```
(S
  (NP_animate_nsubj_main_RC_modified
    (NP_animate_nsubj_rec
      (NP_animate_nsubj_main
        (Det)
        (N_common_animate_nsubj)
      )
    )
    (Rel_pron)
    (VP_RC_object_extracted_theme
      (NP_animate_nsubj_rec
        (NP_animate_nsubj_main
          (Det)
          (N_common_animate_nsubj)
        )
      )
      (V_trans_omissible)
    )
  )
  (VP_main_anim_subj
    (V_trans_not_omissible)
    (NP_dobj
      (NP_animate_dobj
        (Det)
        (N_common_animate_dobj)
      )
    )
  )
)
```

5.
```
(S
  (NP_animate_nsubj_main_RC_modified
    (NP_animate_nsubj_rec
      (NP_animate_nsubj_main
        (Det)
        (N_common_animate_nsubj
      )
      (Rel_pron)
      (VP_RC_agent
        (V_trans_not_omissible)
        (NP_inanimate_dobj_rec
          (NP_inanimate_dobj_RC_modified
            (NP_inanimate_dobj_rec
              (NP_inanimate_dobj
                (Det)
                (N_common_inanimate_dobj)
              )
            )
            (Rel_pron)
            (VP_RC_pass_theme)
          )
        )
      )
    )
  )
  (VP_main_anim_subj
    (V_trans_not_omissible)
    (NP_animate_dobj_rec
      (NP_animate_dobj
        (Det)
        (N_common_animate_dobj)
      )
    )
  )
)
```

6.
```
(S
  (NP_animate_nsubj_main_RC_modified
    (NP_animate_nsubj_main
      (Det)
      (N_common_animate_nsubj)
    )
    (Rel_pron)
    (VP_RC_object_extracted_theme
      (NP_animate_nsubj_rec
        (NP_animate_nsubj_main_RC_modified
          (NP_animate_nsubj_rec
            (NP_animate_nsubj_main
              (Det)
              (N_common_animate_nsubj)
            )
          )
          (Rel_pron)
          (VP_RC_object_extracted_theme
            (NP_animate_nsubj_rec
              (NP_animate_nsubj_main
                (Det)
                (N_common_animate_nsubj)
              )
            )
            (V_trans_not_omissible)
          )
        )
      )
      (V_trans_not_omissible)
    )
  (VP_main_anim_subj
    (V_trans_not_omissible)
    (NP_dobj
      (NP_animate_dobj
        (Det)
        (N_common_animate_dobj)
      )
    )
  )
)
```

In order to derive the sentences, you'll need to explicitly follow this grammar's rules:

```
{rules}
```

Importantly, you'll need to restrict the words to the following lexicon of terminals:

```
{lexicon}
```

{constraints}

Output just the numbered sentences without any extra information.
    """

    return prompt
