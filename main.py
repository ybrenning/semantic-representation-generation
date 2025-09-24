import sys

from generation.src.utils import test_pipeline
from parse import format_sents, parse_sents
from evaluate import evaluate_parse
from prompts.prompt import prompt_from_grammar
from preprocess import handle_null_sents
from utils import get_safe_filename


def generation_loop(grammar_path, n_prompts):
    responses = ""
    for _ in range(n_prompts):
        # Maybe also save the generated prompts?
        prompt = prompt_from_grammar(grammar_path, n_sets=3, k=30)
        print(prompt)

        response = test_pipeline(prompt, temperature=0.4, top_p=0.9)
        responses += response + "\n"

    response_path = "prompts/prompt-newest"

    suffix = (
        f"-{n_prompts}-responses.txt" if n_prompts > 1 else "-response.txt"
    )
    response_path = (
        response_path.split(".")[0] + suffix
    )

    response_path = get_safe_filename(response_path)

    with open(response_path, "w") as f:
        f.write(responses)
        print("Saved response(s) to", response_path)

    return response_path


def main():
    grammar_path = sys.argv[1]
    n_prompts = int(sys.argv[2])
    assert grammar_path.endswith(".irtg"), "Provide IRTG grammar"
    assert isinstance(n_prompts, int), "Provide no. of times to prompt"

    # Generation step
    response_path = generation_loop(grammar_path, n_prompts)

    # Format and parse steps
    sent_path = format_sents(response_path)
    varfree_path = parse_sents(sent_path, grammar_path)

    # Filtering step
    en_lines, vf_lines = handle_null_sents(sent_path, varfree_path)
    print(len(vf_lines))
    assert 0

    # Postprocessing step

    # Evaluation step
    evaluate_parse(
        varfree_path,
        grammar_path,
        show_stats=True,
        show_oov=True
    )


if __name__ == "__main__":
    main()
