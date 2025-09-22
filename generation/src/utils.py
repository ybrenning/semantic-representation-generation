from openai import OpenAI
# from together import Together

from generation.config.config import (
    OPENAI_API_KEY,
    AUDIO_DIR,
    SENTENCES_DIR,
    DEFAULT_MODEL,
    DEFAULT_TTS_MODEL,
    DEFAULT_VOICE,
    themes,
    numbers,
    tenses,
    prompts
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
    print_prompt=False
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
    if print_prompt:
        print("Generated prompt:")
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

    print("\nGenerated response:")
    print("-" * 50)
    print(response)
    print("-" * 50)

    return response


def get_structure(number: int, variation: str, category: str) -> str:
    """Get structure type based on number and variation."""
    # Determine sentence type from file name
    structures = {
        1: 'baseline',
        2: 'control',
        3: 'standard_subject',
        4: 'standard_object',
        5: 'nested_subject',
        6: 'nested_object',
    }

    base_structure = structures.get(number, 'unknown')
    if base_structure == 'unknown':
        print(f"Unknown structure number: {number}")

    # Convert variation to letter index (a=1, b=2, c=3, etc.)
    if not variation:
        variation_num = 'a'  # Default to 'a' if no variation
    else:
        variation_num = variation.lower()

    return f"{base_structure}_{variation_num}"
