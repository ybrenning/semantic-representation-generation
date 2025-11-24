from openai import OpenAI

from generation.config import (
    OPENAI_API_KEY,
    DEFAULT_MODEL,
)

client = OpenAI(api_key=OPENAI_API_KEY)


def gpt4_response(
    prompt,
    model,
    temperature=1.0,
    top_p=1.0,
    frequency_penalty=0.5,
    presence_penalty=0.0
):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
    )

    return chat_completion.choices[0].message.content


def test_pipeline(
    prompt,
    temperature=1.0,
    top_p=1.0,
    theme="basic",
    number="singular",
    tense="present",
    category="relatives",
    verbose=False
):
    """
    Test the pipeline with a single combination of parameters.
    Prints the generated text directly to terminal.

    Args:
        theme (str): Theme key from themes dictionary
        number (str): Number key from numbers dictionary
        tense (str): Tense key from tenses dictionary
        category (str): Category key from prompts dictionary
        print_prompt (bool) : True to print the prompt
    """
    if verbose:
        print("Prompt:")
        print("-" * 50)
        print(prompt)
        print("-" * 50)

    response = gpt4_response(
        prompt=prompt,
        model=DEFAULT_MODEL,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=0.1,
        presence_penalty=0.
    )

    if verbose:
        print("\nGenerated response:")
        print("-" * 50)
        print(response)
        print("-" * 50)

    return response
