# Grammars

## Structure

The `base` directory contains some IRTG grammars from the original [SLOG](https://github.com/bingzhilee/slog) repository. Some slight modifications have been added, which are mentioned in comments in the non-preprocessed files.

The `batch` directory contains the grammars that allow for the generation of the six sentence types. We have one "general" grammar designed to be able to generate and accept all six sentence types (this is used mainly for prompting and later for checking OOV sentences), and we have six distinct "control" grammars, used in the parsing and evaluation steps. Each grammar is meant to consist of a minimal amount of rules such that it only runs a valid parse on sentences following its specifications. This is used in the evaluation step in order to determine which sentences have been correctly generated and which sets to keep or to discard.

The `slog` directorz contains grammars that are used to generate SLOG-like datasets. For example, the `slog-rec_pp` grammar accepts sentences similar to the recursive PP sentences contained in SLOG. For recursive grammars such as this one, the recursion depth is contained in the name -- `slog-rec_pp_2` only accepts sentences with exactly **two** prepositional phrases, and so on.

## Grammar Pipeline

The `combine_grammars.py` script is a helper script that was used to combine the main and relative clause grammars from SLOG into a single IRTG file.
This large grammar is essentially the "base grammar", used in the batch generation case. It is essentially designed to cover all six different sentence types and is also referred to as the "prompt grammar" as this is the single grammar that is used in the body of the prompt.

The `cogs_preprocess.py` script is adapted from SLOG and is used in conjunction with `specify_grammar.irtg` in order to dynamically render the final grammar from the original IRTG files. The naming convention for the outputs of this script is usually to prepend `preprocessed-` to the grammar name to avoid confusion with the original IRTG.

```bash
$ python3 cogs_preprocess.py slog/slog-rec_pp_2.irtg
```

This produces a synchronous probabilistic context-free grammar with rules like this:

```bash
S! -> r1792(NP_animate_nsubj, VP_external) 	[0.49]
  [english] *(?1, ?2)
  [semantics] pre_agent(?2, ?1)
```

For the generation step, we only need the *English* part of the grammar -- the *Semantics* will be used in order to parse the generated sentences later on.

So, we use `irtg2ebnf.py` to simply convert the IRTG format into the English-only rules which will be part of the prompt later on.

For example, we extract the English part of the preprocessed grammar above like this:

```bash
$ python3 irtg2ebnf.py slog/preprocessed-slog-rec_pp_2.irtg
```

The resulting English grammar always has the same name as the original file, so in this example, `preprocessed-slog-rec_pp_2.ebnf`.
