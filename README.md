# Semantic Representation Generation

This project concerns itself with creating a dataset generation approach based on a probabilistic synchronous context-free grammar (SCFG). The grammar used follows rules from the SLOG dataset [(Li et al., 2023)](https://arxiv.org/abs/2310.15040), a structural generalization benchmark for semantic parsing. The goal is to adapt the rule-based approach in such a manner that it is capable of not only generating syntactically but also semantically meaningful sentences.

## Workflow

![workflow](img/workflow.png)

The base grammars, from Li et al. (2023) are currently in the IRTG (Interpreted Regular Tree Grammar) format, which we separate into an English grammar for the generation step and a Semantics grammar for the annotation and evaluation steps.

This part of the workflow can be found in `grammars` directory of this repository, which also makes use of SLOG's original [preprocessing source code](https://github.com/bingzhilee/SLOG/tree/main/generation_scripts/grammars). This also applies to the [postprocessing code](https://github.com/bingzhilee/SLOG/tree/main/generation_scripts/varfree2cogs_converter) used in later parts of the workflow.

The resulting English grammar can then simply be used as part of a GPT model prompt (more information can be found in the `prompts` directory), or with a constrained decoding library in order to generate English sentences.

These English sentences must then be annotated in order to obtain a semantic representation for each one. To this end, we use the Alto parser employed by SLOG in order to create semantic representations for each sentence. These are generated in the so-called *variable-free logical form* (LF), and are converted to the unambiguous COGS LF using the postprocessing script adapted from Li et al.

Here is an example of the semantic representation in both LFs for the sentence "A cat wanted to sleep.":

```bash
want(agent=cat, xcomp=sleep(agent=cat))  # Variable-free LF 

cat(x_1) AND want.agent(x_2,x_1) AND want.xcomp(x_2, x_4) AND sleep.agent(x_4,x_1)  # COGS LF
```

If a sentence does not have a valid derivation following the grammar, the parser returns `<null>`. This can be used as part of an evaluation step where we determine how many of the generated sentences actually follow the provided grammar.

The result is a corpus of English sentences, each one paired with their semantic representation. This workflow should be applicable both for training and test sets -- for generalization (test), the main difference lies in the grammar/prompt used for the sentence generation.

## Prompting

The overall idea for all prompts is to constrain `gpt-4o` to a context-free grammar while generating sentences following the following six structures:

1) Baseline (SV): Simple Subject-Verb structure
2) Control (S Prep V): Subject with Prepositional_Clause and Verb
3) Standard-Subject (S RelSubj V): Subject with Subject Relative Clause and Verb
4) Standard-Object (S RelObj V): Subject with Object Relative Clause and Verb
5) Nested-Subject (S [RelSubj[Rel]] V): Subject with two embedded Relative Clauses, the first one being a Subject Relative Clause, and Verb
6) Nested-Object (S [RelObj[Rel]] V): Subject with two embedded Relative Clauses, the first one being an Object Relative Clause, and Verb

For example:

1. The doctor examines the patient.
2. The doctor in the room examines the patient.
3. The doctor who studied hard examines the patient.
4. The doctor who the parent called examines the patient.
5. The doctor who read the report that was on the desk examines the patient.
6. The doctor who the mother who the school called trusts examines the patient.

## Run pipeline

The main part of the workflow can be run from a single script by providing a `grammar_path` to an IRTG file and `n_prompts`, the number of times to repeat the generation request. Based on this, the script creates a prompt from the grammar, passes it to `gpt-4o`, saves the raw text response, cleans and formats the sentences to correspond with the SLOG English representation, runs the parser on the sentences to produce the semantic representations, and finally computes various evaluation scores.

### Install dependencies 

Install the required dependencies from a virtual environment:

```bash
$ python -m venv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
```

Run the script with the preprocessed CFG and the number of times to prompt as a command line argument:

```bash
$ python3 main.py grammars/preprocessed-combined.irtg 10
``` 

Similarly, the `parse` and `evaluate` modules can also be executed as scripts separately. Note that the step is only executable if the files of the previous pipeline steps have already been generated. For example, we can use the `evaluate` script as follows:

```bash
$ python3 evaluate.py batch generation/responses/batch-2-responses-1.txt --verbose 

Parse accuracies
╒═════════════════╤════════════╕
│ Sentence Type   │ Accuracy   │
╞═════════════════╪════════════╡
│ Type 1          │ 100.00%    │
├─────────────────┼────────────┤
│ Type 2          │ 100.00%    │
├─────────────────┼────────────┤
│ Type 3          │ 100.00%    │
├─────────────────┼────────────┤
│ Type 4          │ 100.00%    │
├─────────────────┼────────────┤
│ Type 5          │ 100.00%    │
├─────────────────┼────────────┤
│ Type 6          │ 100.00%    │
╘═════════════════╧════════════╛

Batch Accuracy: 100.00%

Sentences w/ consistent main S/V
╒═════════════════╤════════════╕
│ Sentence Type   │ Accuracy   │
╞═════════════════╪════════════╡
│ Type 1          │ 100.00%    │
├─────────────────┼────────────┤
│ Type 2          │ 100.00%    │
├─────────────────┼────────────┤
│ Type 3          │ 100.00%    │
├─────────────────┼────────────┤
│ Type 4          │ 100.00%    │
├─────────────────┼────────────┤
│ Type 5          │ 100.00%    │
├─────────────────┼────────────┤
│ Type 6          │ 100.00%    │
╘═════════════════╧════════════╛

Batch Accuracy: 100.00%

Non-repetition sentences
╒═════════════════╤════════════╕
│ Sentence Type   │ Accuracy   │
╞═════════════════╪════════════╡
│ Type 1          │ 100.00%    │
├─────────────────┼────────────┤
│ Type 2          │ 100.00%    │
├─────────────────┼────────────┤
│ Type 3          │ 100.00%    │
├─────────────────┼────────────┤
│ Type 4          │ 100.00%    │
├─────────────────┼────────────┤
│ Type 5          │ 87.50%     │
├─────────────────┼────────────┤
│ Type 6          │ 100.00%    │
╘═════════════════╧════════════╛

Batch Accuracy: 87.50%
```

## Grammars

### English sentence grammar

The sentences are generated based on the `english` part of SLOG's SCFG. We use SLOG's preprocess script in order to dynamically generate an IRTG file based on an SCFG's rules and a lexicon (vocabulary) of terminals.

We convert this preprocessed file into the more commonly used EBNF (Extended Backus–Naur form) format. This can then be used as part of a prompt on a GPT-based model or for constrained decoding using a library such as `outlines`.

### Semantic representation grammar

In SLOG, this grammar is used synchronously with the English sentence grammar in order to produce a semantic representation for each sentence.

Since this approach makes use of LLMs to generate the English sentences, we have to annotate them retrospectively as opposed to in parallel. Luckily, the Alto library allows for parsing of an unannotated corpus based on a given grammar.

For example: 

```bash
$ java -cp ../alto/build/libs/alto-2.3.8-SNAPSHOT-all.jar de.up.ling.irtg.script.ParsingEvaluator -g grammars/preprocessed-main.irtg -I english -O semantics=cogs --no-derivations test-alto.txt
```
