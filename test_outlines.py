import outlines
from outlines.types import CFG
from transformers import AutoModelForCausalLM, AutoTokenizer

# Define the model you want to use
model_name = "HuggingFaceTB/SmolLM2-135M-Instruct"

# Create a HuggingFace model and tokenizer
hf_model = AutoModelForCausalLM.from_pretrained(model_name)
hf_tokenizer = AutoTokenizer.from_pretrained(model_name)

# Create an Outlines model
model = outlines.from_transformers(hf_model, hf_tokenizer)

# Define your Lark grammar as string
arithmetic_grammar = """
    ?start: sum

    ?sum: product
        | sum "+" product   -> add
        | sum "-" product   -> sub

    ?product: atom
        | product "*" atom  -> mul
        | product "/" atom  -> div

    ?atom: NUMBER           -> number
        | "-" atom         -> neg
        | "(" sum ")"

    %import common.NUMBER
    %import common.WS_INLINE

    %ignore WS_INLINE
"""

print(arithmetic_grammar)
# Generate an arithmetic operation
result = model(
    "Write an arithmetic operation",
    CFG(arithmetic_grammar)
)
print(result) # '2 + 3'
