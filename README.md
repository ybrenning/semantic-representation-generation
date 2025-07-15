# Semantic Representation Generation

Currently, this repo aims to implement the following workflow:

![workflow](img/workflow.png)

The base grammars are currently in an IRTG format, which needs to be converted to EBNF for the format specifications of the Lark library. The IRTG files must first be preprocessed by the script `cogs-preprocess.py`, as parts of the files use Jinja to dynamically generate rule numbers, terminals, and probabilities.

The resulting EBNF-formatted grammar can then be used to prompt a GPT model (more information can be found in the `prompts` directory), or be used with a constrained decoding library in order to generate English sentences.

These English sentences must then be annotated in order to obtain a semantic representation for each one. To this end, the Alto tool used by SLOG should be able to use the pre-existing semantic representation grammar in order to annotate the corpus.

The result should be a corpus of English sentences paired with their semantic represenations. This workflow should be applicable both for training and test sets -- for generalization (test), the difference should be in the grammar/prompt used for the sentence generation.
