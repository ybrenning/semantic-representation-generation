# Semantic Representation Generation

## Workflow

![workflow](img/workflow.png)

The base grammars, adapted from [Li et al. (2023)](https://arxiv.org/abs/2310.15040), are currently in an IRTG format, which needs to be converted to EBNF for the format specifications of the Lark library. The IRTG files must first be preprocessed by the script `cogs-preprocess.py`, as parts of the files use Jinja to dynamically generate rule numbers, terminals, and probabilities.

This part of the workflow can be found in `grammars` directory of this repository, which makes use of SLOG's original [preprocessing source code](https://github.com/bingzhilee/SLOG/tree/main/generation_scripts/grammars). This also applies to the [postprocessing code](https://github.com/bingzhilee/SLOG/tree/main/generation_scripts/varfree2cogs_converter) used in later parts of the workflow.

The resulting preprocessed file is then converted to the EBNF format, which can then be used to prompt a GPT model (more information can be found in the `prompts` directory), or be used with a constrained decoding library in order to generate English sentences.

These English sentences must then be annotated in order to obtain a semantic representation for each one. To this end, we use the Alto parser employed by SLOG in order to create semantic representations for each sentences. These are created in the so-called *variable-free logical form* (LF), and are converted to the unambiguous COGS LF using the postprocessing script adapted from Li et al.

Here is an example of the semantic representation in both LFs for the sentence "A cat wanted to sleep.":

```bash
want(agent=cat, xcomp=sleep(agent=cat))  # Variable-free LF 

cat(x_1) AND want.agent(x_2,x_1) AND want.xcomp(x_2, x_4) AND sleep.agent(x_4,x_1)  # COGS LF
```

The result is a corpus of English sentences, each one paired with their semantic representation. This workflow should be applicable both for training and test sets -- for generalization (test), the difference lies in the grammar/prompt used for the sentence generation.

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

Similarly, the `parse` and `evaluate` modules can also be executed as scripts separately:

```bash
$ python3 evaluate.py data/varfree_lf/prompt-newest-10-responses-18.txt grammars/preprocessed-combined.irtg 

-----------
Total OOV percentage: 1 / 156 = 0.64%
OOV sentences: 1 / 180 = 0.56%
-----------
Line parse accuracy: 175/180 = 97.22%
Batch parse accuracy: 25/30 = 83.33%
Batch form accuracy: 25/30 = 83.33%
-----------
Accuracy per sentence type:
  Sentence 1: 30/30= 100.00%
  Sentence 2: 28/30= 93.33%
  Sentence 3: 30/30= 100.00%
  Sentence 4: 30/30= 100.00%
  Sentence 5: 27/30= 90.00%
  Sentence 6: 30/30= 100.00%
-----------
```

## Grammars

### English sentence grammar

The sentences are generated based on the `english` part of SLOG's synchronous context-free grammar (SCFG). We use SLOG's preprocess script in order to dynamically generate an IRTG (Interpreted Regular Tree Grammart) file based on an SCFG's rules and a lexicon (vocabulary) of terminals.

We convert this preprocessed file into the more commonly used EBNF (Extended Backus–Naur form) format. This can then be used as part of a prompt on a GPT-based model or for constrained decoding using a library such as `outlines`.

### Semantic representation grammar

In SLOG, this grammar is used synchronously with the English sentence grammar in order to produce a semantic representation for each sentence.

Since this approach makes use of LLMs to generate the English sentences, we have to annotate them retrospectively as opposed to in parallel. Luckily, the Alto library allows for parsing of an unannotated corpus based on a given grammar.

For example: 

```bash
$ java -cp ../alto/build/libs/alto-2.3.8-SNAPSHOT-all.jar de.up.ling.irtg.script.ParsingEvaluator -g grammars/preprocessed-main.irtg -I english -O semantics=cogs --no-derivations test-alto.txt
```
