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


def process_task(task):
    try:
        category, theme, number, tense = task
        theme_description = themes[theme]
        number_description = numbers[number]
        tense_description = tenses[tense]
        savepath = SENTENCES_DIR / "V2" / category / f"{theme}_{number}_{tense}.txt"

        if savepath.exists():
            return

        # special_prompt = prompts[category]
        special_prompt = """
I would like you to generate English sentences of the following six forms.

1) Baseline (SV): Simple Subject-Verb structure
2) Control (S Prep V): Subject with Prepositional_Clause and Verb
3) Standard-Subject (S RelSubj V): Subject with Subject Relative Clause and Verb
4) Standard-Object (S RelObj V): Subject with Object Relative Clause and Verb
5) Nested-Subject (S [RelSubj[Rel]] V): Subject with two embedded Relative Clauses, the first one being a Subject Relative Clause, and Verb
6) Nested-Object (S [RelObj[Rel]] V): Subject with two embedded Relative Clauses, the first one being an Object Relative Clause, and Verb

I would like the sentences to follow this EBNF grammar:

```
S : NP_animate_nsubj VP_external | VP_internal | NP_inanimate_nsubjpass VP_passive | NP_animate_nsubjpass VP_passive_dat

VP_external : V_unerg | V_unacc NP_dobj | V_trans_omissible | V_trans_omissible NP_dobj | V_trans_not_omissible NP_dobj | V_inf_taking INF V_inf | V_dat NP_inanimate_dobj PP_iobj | V_dat NP_animate_iobj NP_inanimate_dobj | V_cp_taking C S!

VP_internal : NP_unacc_subj V_unacc

VP_passive : AUX V_trans_not_omissible_pp | AUX V_trans_not_omissible_pp BY NP_animate_nsubj | AUX V_trans_omissible_pp | AUX V_trans_omissible_pp BY NP_animate_nsubj | AUX V_unacc_pp | AUX V_unacc_pp BY NP_animate_nsubj | AUX V_dat_pp PP_iobj | AUX V_dat_pp PP_iobj BY NP_animate_nsubj

VP_passive_dat : AUX V_dat_pp NP_inanimate_dobj | AUX V_dat_pp NP_inanimate_dobj BY NP_animate_nsubj

NP_dobj : NP_inanimate_dobj | NP_animate_dobj

NP_unacc_subj : NP_inanimate_dobj_noPP | NP_animate_dobj_noPP

NP_animate_dobj_noPP : Det N_common_animate_dobj | N_prop_dobj

NP_animate_dobj : Det N_common_animate_dobj | Det N_common_animate_dobj PP_loc | N_prop_dobj

NP_animate_iobj : Det N_common_animate_iobj | N_prop_iobj

NP_animate_nsubj : Det N_common_animate_nsubj | N_prop_nsubj

NP_animate_nsubjpass : Det N_common_animate_nsubjpass | N_prop_nsubjpass

NP_inanimate_dobj : Det N_common_inanimate_dobj | Det N_common_inanimate_dobj PP_loc

NP_inanimate_dobj_noPP : Det N_common_inanimate_dobj

NP_inanimate_nsubjpass : Det N_common_inanimate_nsubjpass

NP_on : Det N_on PP_loc | Det N_on

NP_in : Det N_in PP_loc | Det N_in

NP_beside : Det N_beside PP_loc | Det N_beside

PP_loc : P_on NP_on | P_in NP_in | P_beside NP_beside

PP_iobj : P_iobj NP_animate_iobj
```

The terminals being *words* that are up to you to infer based on the grammar.

Do not generate sentences that are too close to the exemple sentences. The goal is to generate new and original sentences. I don't want all sentences to have 'in the room' or 'on the desk'.

Output only the sentences themselves, without any additional information. Please do the above task a total of five times.
        """
        prompt = get_prompt(
            number=number_description,
            tense=tense_description,
            theme=theme_description,
            n=1,
            special_prompt=special_prompt
        )

        response = gpt4_response(
            prompt=prompt,
            model=DEFAULT_MODEL,
        )

        print(response)
        # savepath.parent.mkdir(parents=True, exist_ok=True)
        # with open(savepath, "w") as f:
        #     f.write(response)
        # print(f"Saved {savepath}")
    except Exception as e:
        print(f"Error with {task}: {e}")


def gpt4_response(
    prompt,
    model,
    temperature=1.0,
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
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
    )

    return chat_completion.choices[0].message.content


def llama_response(prompt, model, temperature=1.2): #, top_p=0.9, top_k=50, repetition_penalty=1.0)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        # top_p=top_p,
        # top_k=top_k,
        # repetition_penalty=repetition_penalty  
    )
    return response.choices[0].message.content


def test_pipeline(
    prompt,
    temperature=1.0,
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
