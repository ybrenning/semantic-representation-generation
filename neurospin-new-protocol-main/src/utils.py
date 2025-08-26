import os
import re
from pathlib import Path
from openai import OpenAI
# from together import Together
from typing import List, Union
from config.config import (
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


def gpt4_response(prompt, model, frequency_penalty=0.5, presence_penalty=0.0):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model,
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


def get_prompt(
        number: str, tense: str, theme: str, n: int, special_prompt: str
) -> str:
    prompt = f"""You are an expert linguist. You'll be asked to generate sets of sentences following the instructions below:

1. Number: {number}.

2. Tense: {tense}. Limit yourself to simple tenses (present simple, past simple)

3. Theme: {theme}.

4. Important constraints on the sentences:
- must start on a new line with a number followed by a period.
- must NOT contain proper nouns or commas.
- must NOT exceed 12 words in length.
- must NOT end with a verb.

Generate {n} set of sentences, each with six variations, adhering to the following guidelines:

Make sure to make the sentences generated as close as possible to each other: a singular object should be a singular object in other variations.

{special_prompt}
"""
    prompt = special_prompt
    return prompt


def test_pipeline(
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
    print(f"\nTesting pipeline with:\nTheme: {theme}\nNumber: {number}\nTense: {tense}\nCategory: {category}\n")
    print("-" * 50)

    theme_description = themes[theme]
    number_description = numbers[number]
    tense_description = tenses[tense]

    special_prompt = """
You are an expert linguist. I would like you to look at the following grammar in EBNF format:

```
Det  : the | a

AUX  : was

C  : that

BY  : by

INF  : to

N_common_animate_dobj  : girl | boy | cat | dog | baby | child | teacher | frog | chicken | mouse | lion | monkey | bear | giraffe | horse | bird | duck | bunny | butterfly | penguin | student | professor | monster | hero | sailor | lawyer | customer | scientist | princess | president | cow | crocodile | goose | hen | deer | donkey | bee | fly | kitty | tiger | wolf | zebra | mother | father | patient | manager | director | king | queen | kid | fish | moose | pig | pony | puppy | sheep | squirrel | lamb | turkey | turtle | doctor | pupil | prince | driver | consumer | writer | farmer | friend | judge | visitor | guest | servant | chief | citizen | champion | prisoner | captain | soldier | passenger | tenant | politician | resident | buyer | spokesman | governor | guard | creature | coach | producer | researcher | guy | dealer | duke | tourist | landlord | human | host | priest | journalist | poet

N_common_animate_iobj  : girl | boy | cat | dog | baby | child | teacher | frog | chicken | mouse | lion | monkey | bear | giraffe | horse | bird | duck | bunny | butterfly | penguin | student | professor | monster | hero | sailor | lawyer | customer | scientist | princess | president | cow | crocodile | goose | hen | deer | donkey | bee | fly | kitty | tiger | wolf | zebra | mother | father | patient | manager | director | king | queen | kid | fish | moose | pig | pony | puppy | sheep | squirrel | lamb | turkey | turtle | doctor | pupil | prince | driver | consumer | writer | farmer | friend | judge | visitor | guest | servant | chief | citizen | champion | prisoner | captain | soldier | passenger | tenant | politician | resident | buyer | spokesman | governor | guard | creature | coach | producer | researcher | guy | dealer | duke | tourist | landlord | human | host | priest | journalist | poet

N_common_animate_nsubj  : girl | boy | cat | dog | baby | child | teacher | frog | chicken | mouse | lion | monkey | bear | giraffe | horse | bird | duck | bunny | butterfly | penguin | student | professor | monster | hero | sailor | lawyer | customer | scientist | princess | president | cow | crocodile | goose | hen | deer | donkey | bee | fly | kitty | tiger | wolf | zebra | mother | father | patient | manager | director | king | queen | kid | fish | moose | pig | pony | puppy | sheep | squirrel | lamb | turkey | turtle | doctor | pupil | prince | driver | consumer | writer | farmer | friend | judge | visitor | guest | servant | chief | citizen | champion | prisoner | captain | soldier | passenger | tenant | politician | resident | buyer | spokesman | governor | guard | creature | coach | producer | researcher | guy | dealer | duke | tourist | landlord | human | host | priest | journalist | poet

N_common_animate_nsubjpass  : girl | boy | cat | dog | baby | child | teacher | frog | chicken | mouse | lion | monkey | bear | giraffe | horse | bird | duck | bunny | butterfly | penguin | student | professor | monster | hero | sailor | lawyer | customer | scientist | princess | president | cow | crocodile | goose | hen | deer | donkey | bee | fly | kitty | tiger | wolf | zebra | mother | father | patient | manager | director | king | queen | kid | fish | moose | pig | pony | puppy | sheep | squirrel | lamb | turkey | turtle | doctor | pupil | prince | driver | consumer | writer | farmer | friend | judge | visitor | guest | servant | chief | citizen | champion | prisoner | captain | soldier | passenger | tenant | politician | resident | buyer | spokesman | governor | guard | creature | coach | producer | researcher | guy | dealer | duke | tourist | landlord | human | host | priest | journalist | poet

N_common_animate_dobj_targeted  : hedgehog

N_common_animate_dobj_targeted_primitive  : shark

N_prop_dobj_targeted  : Lina

N_prop_dobj_targeted_primitive  : Paula

N_common_animate_nsubj_targeted  : hedgehog

N_common_animate_nsubj_targeted_primitive  : shark

N_prop_nsubj_targeted  : Lina

N_prop_nsubj_targeted_primitive  : Paula

N_common_inanimate_dobj  : cake | donut | cookie | box | rose | drink | raisin | melon | sandwich | strawberry | ball | balloon | bat | block | book | crayon | chalk | doll | game | glue | lollipop | hamburger | banana | biscuit | muffin | pancake | pizza | potato | pretzel | pumpkin | sweetcorn | yogurt | pickle | jigsaw | pen | pencil | present | toy | cracker | brush | radio | cloud | mandarin | hat | basket | plant | flower | chair | spoon | pillow | gumball | scarf | shoe | jacket | hammer | bucket | knife | cup | plate | towel | bottle | bowl | can | clock | jar | penny | purse | soap | toothbrush | watch | newspaper | fig | bag | wine | key | weapon | brain | tool | crown | ring | leaf | fruit | mirror | beer | shirt | guitar | chemical | seed | shell | brick | bell | coin | button | needle | molecule | crystal | flag | nail | bean | liver

N_common_inanimate_nsubjpass  : cake | donut | cookie | box | rose | drink | raisin | melon | sandwich | strawberry | ball | balloon | bat | block | book | crayon | chalk | doll | game | glue | lollipop | hamburger | banana | biscuit | muffin | pancake | pizza | potato | pretzel | pumpkin | sweetcorn | yogurt | pickle | jigsaw | pen | pencil | present | toy | cracker | brush | radio | cloud | mandarin | hat | basket | plant | flower | chair | spoon | pillow | gumball | scarf | shoe | jacket | hammer | bucket | knife | cup | plate | towel | bottle | bowl | can | clock | jar | penny | purse | soap | toothbrush | watch | newspaper | fig | bag | wine | key | weapon | brain | tool | crown | ring | leaf | fruit | mirror | beer | shirt | guitar | chemical | seed | shell | brick | bell | coin | button | needle | molecule | crystal | flag | nail | bean | liver

N_common_inanimate_nsubj  : cake | donut | cookie | box | rose | drink | raisin | melon | sandwich | strawberry | ball | balloon | bat | block | book | crayon | chalk | doll | game | glue | lollipop | hamburger | banana | biscuit | muffin | pancake | pizza | potato | pretzel | pumpkin | sweetcorn | yogurt | pickle | jigsaw | pen | pencil | present | toy | cracker | brush | radio | cloud | mandarin | hat | basket | plant | flower | chair | spoon | pillow | gumball | scarf | shoe | jacket | hammer | bucket | knife | cup | plate | towel | bottle | bowl | can | clock | jar | penny | purse | soap | toothbrush | watch | newspaper | fig | bag | wine | key | weapon | brain | tool | crown | ring | leaf | fruit | mirror | beer | shirt | guitar | chemical | seed | shell | brick | bell | coin | button | needle | molecule | crystal | flag | nail | bean | liver

N_prop_dobj  : Emma | Liam | Olivia | Noah | Ava | William | Isabella | James | Sophia | Oliver | Charlotte | Benjamin | Mia | Elijah | Amelia | Lucas | Harper | Mason | Evelyn | Logan | Abigail | Alexander | Emily | Ethan | Elizabeth | Jacob | Mila | Michael | Ella | Daniel | Avery | Henry | Sofia | Jackson | Camila | Sebastian | Aria | Aiden | Scarlett | Matthew | Victoria | Samuel | Madison | David | Luna | Joseph | Grace | Carter | Chloe | Owen | Penelope | Wyatt | Layla | John | Riley | Jack | Zoey | Luke | Nora | Jayden | Lily | Dylan | Eleanor | Grayson | Hannah | Levi | Lillian | Isaac | Addison | Gabriel | Aubrey | Julian | Ellie | Mateo | Stella | Anthony | Natalie | Jaxon | Zoe | Lincoln | Leah | Joshua | Hazel | Christopher | Violet | Andrew | Aurora | Theodore | Savannah | Caleb | Audrey | Ryan | Brooklyn | Asher | Bella | Nathan | Claire | Thomas | Skylar | Leo

N_prop_iobj  : Emma | Liam | Olivia | Noah | Ava | William | Isabella | James | Sophia | Oliver | Charlotte | Benjamin | Mia | Elijah | Amelia | Lucas | Harper | Mason | Evelyn | Logan | Abigail | Alexander | Emily | Ethan | Elizabeth | Jacob | Mila | Michael | Ella | Daniel | Avery | Henry | Sofia | Jackson | Camila | Sebastian | Aria | Aiden | Scarlett | Matthew | Victoria | Samuel | Madison | David | Luna | Joseph | Grace | Carter | Chloe | Owen | Penelope | Wyatt | Layla | John | Riley | Jack | Zoey | Luke | Nora | Jayden | Lily | Dylan | Eleanor | Grayson | Hannah | Levi | Lillian | Isaac | Addison | Gabriel | Aubrey | Julian | Ellie | Mateo | Stella | Anthony | Natalie | Jaxon | Zoe | Lincoln | Leah | Joshua | Hazel | Christopher | Violet | Andrew | Aurora | Theodore | Savannah | Caleb | Audrey | Ryan | Brooklyn | Asher | Bella | Nathan | Claire | Thomas | Skylar | Leo

N_prop_nsubj  : Emma | Liam | Olivia | Noah | Ava | William | Isabella | James | Sophia | Oliver | Charlotte | Benjamin | Mia | Elijah | Amelia | Lucas | Harper | Mason | Evelyn | Logan | Abigail | Alexander | Emily | Ethan | Elizabeth | Jacob | Mila | Michael | Ella | Daniel | Avery | Henry | Sofia | Jackson | Camila | Sebastian | Aria | Aiden | Scarlett | Matthew | Victoria | Samuel | Madison | David | Luna | Joseph | Grace | Carter | Chloe | Owen | Penelope | Wyatt | Layla | John | Riley | Jack | Zoey | Luke | Nora | Jayden | Lily | Dylan | Eleanor | Grayson | Hannah | Levi | Lillian | Isaac | Addison | Gabriel | Aubrey | Julian | Ellie | Mateo | Stella | Anthony | Natalie | Jaxon | Zoe | Lincoln | Leah | Joshua | Hazel | Christopher | Violet | Andrew | Aurora | Theodore | Savannah | Caleb | Audrey | Ryan | Brooklyn | Asher | Bella | Nathan | Claire | Thomas | Skylar | Leo

N_prop_nsubjpass  : Emma | Liam | Olivia | Noah | Ava | William | Isabella | James | Sophia | Oliver | Charlotte | Benjamin | Mia | Elijah | Amelia | Lucas | Harper | Mason | Evelyn | Logan | Abigail | Alexander | Emily | Ethan | Elizabeth | Jacob | Mila | Michael | Ella | Daniel | Avery | Henry | Sofia | Jackson | Camila | Sebastian | Aria | Aiden | Scarlett | Matthew | Victoria | Samuel | Madison | David | Luna | Joseph | Grace | Carter | Chloe | Owen | Penelope | Wyatt | Layla | John | Riley | Jack | Zoey | Luke | Nora | Jayden | Lily | Dylan | Eleanor | Grayson | Hannah | Levi | Lillian | Isaac | Addison | Gabriel | Aubrey | Julian | Ellie | Mateo | Stella | Anthony | Natalie | Jaxon | Zoe | Lincoln | Leah | Joshua | Hazel | Christopher | Violet | Andrew | Aurora | Theodore | Savannah | Caleb | Audrey | Ryan | Brooklyn | Asher | Bella | Nathan | Claire | Thomas | Skylar | Leo

N_on  : table | stage | bed | chair | stool | road | tree | box | surface | seat | speaker | computer | rock | boat | cabinet | TV | plate | desk | bowl | bench | shelf | cloth | piano | bible | leaflet | sheet | cupboard | truck | tray | notebook | blanket | deck | coffin | log | ladder | barrel | rug | canvas | tiger | towel | throne | booklet | sock | corpse | sofa | keyboard | book | pillow | pad | train | couch | bike | pedestal | platter | paper | rack | board | panel | tripod | branch | machine | floor | napkin | cookie | block | cot | device | yacht | dog | mattress | ball | stand | stack | windowsill | counter | cushion | hanger | trampoline | gravel | cake | carpet | plaque | boulder | leaf | mound | bun | dish | cat | podium | tabletop | beach | bag | glacier | brick | crack | vessel | futon | turntable | rag | chessboard

N_in  : house | room | car | garden | box | cup | glass | bag | vehicle | hole | cabinet | bottle | shoe | storage | cot | vessel | pot | pit | tin | can | cupboard | envelope | nest | bush | coffin | drawer | container | basin | tent | soup | well | barrel | bucket | cage | sink | cylinder | parcel | cart | sack | trunk | wardrobe | basket | bin | fridge | mug | jar | corner | pool | blender | closet | pile | van | trailer | saucepan | truck | taxi | haystack | dumpster | puddle | bathtub | pod | tub | trap | bun | microwave | bookstore | package | cafe | train | castle | bunker | vase | backpack | tube | hammock | stadium | backyard | swamp | monastery | refrigerator | palace | cubicle | crib | condo | tower | crate | dungeon | teapot | tomb | casket | jeep | shoebox | wagon | bakery | fishbowl | kennel | china | spaceship | penthouse | pyramid

N_beside  : table | stage | bed | chair | book | road | tree | machine | house | seat | speaker | computer | rock | car | box | cup | glass | bag | flower | boat | vehicle | key | painting | cabinet | TV | bottle | cat | desk | shoe | mirror | clock | bench | bike | lamp | lion | piano | crystal | toy | duck | sword | sculpture | rod | truck | basket | bear | nest | sphere | bush | surgeon | poster | throne | giant | trophy | hedge | log | tent | ladder | helicopter | barrel | yacht | statue | bucket | skull | beast | lemon | whale | cage | gardner | fox | sink | trainee | dragon | cylinder | monk | bat | headmaster | philosopher | foreigner | worm | chemist | corpse | wolf | torch | sailor | valve | hammer | doll | genius | baron | murderer | bicycle | keyboard | stool | pepper | warrior | pillar | monkey | cassette | broker | bin

P_on  : on

P_in  : in

P_beside  : beside

P_iobj  : to

Rel_pron  : that

WHO  : Who

WHAT  : What

AUX_did  : did

V_trans_omissible  : ate | painted | drew | cleaned | cooked | dusted | hunted | nursed | sketched | juggled | called | heard | packed | saw | noticed | studied | examined | observed | knew | investigated

V_trans_omissible_inf  : eat | paint | draw | clean | cook | dust | hunt | nurse | sketch | juggle | call | hear | pack | see | notice | study | examine | observe | know | investigate

V_trans_omissible_pp  : eaten | painted | drawn | cleaned | cooked | dusted | hunted | nursed | sketched | juggled | called | heard | packed | seen | noticed | studied | examined | observed | known | investigated

V_trans_not_omissible  : liked | helped | found | loved | poked | admired | adored | appreciated | missed | respected | threw | tolerated | valued | worshipped | discovered | held | stabbed | touched | pierced | tossed

V_trans_not_omissible_inf  : like | help | find | love | poke | admire | adore | appreciate | miss | respect | throw | tolerate | value | worship | discover | hold | stab | touch | pierce | toss

V_trans_not_omissible_pp  : liked | helped | found | loved | poked | admired | adored | appreciated | missed | respected | thrown | tolerated | valued | worshipped | discovered | held | stabbed | touched | pierced | tossed

V_cp_taking  : liked | hoped | said | noticed | believed | confessed | declared | proved | thought | admired | appreciated | respected | supported | tolerated | valued | wished | dreamed | expected | imagined | meant

V_cp_taking_inf  : like | hope | say | notice | believe | confess | declare | prove | think | admire | appreciate | respect | support | tolerate | value | wish | dream | expect | imagine | mean

V_inf_taking  : wanted | preferred | needed | intended | tried | attempted | planned | expected | hoped | wished | craved | liked | hated | loved | enjoyed | dreamed | meant | longed | yearned | itched

V_unacc  : rolled | froze | burned | shortened | floated | grew | slid | broke | crumpled | split | changed | snapped | disintegrated | collapsed | decomposed | doubled | improved | inflated | enlarged | reddened

V_unacc_inf  : roll | freeze | burn | shorten | float | grow | slide | break | crumple | split | change | snap | disintegrate | collapse | decompose | double | improve | inflate | enlarge | redden

V_unacc_pp  : rolled | frozen | burned | shortened | floated | grown | slid | broken | crumpled | split | changed | snapped | disintegrated | collapsed | decomposed | doubled | improved | inflated | enlarged | reddened

V_unerg  : slept | smiled | laughed | sneezed | cried | talked | danced | jogged | walked | ran | napped | snoozed | screamed | stuttered | frowned | giggled | scoffed | snored | smirked | gasped

V_inf  : walk | run | sleep | sneeze | nap | eat | read | cook | hunt | paint | talk | dance | giggle | jog | smirk | call | sketch | dust | clean | investigate

V_dat  : gave | lent | sold | offered | fed | passed | sent | rented | served | awarded | brought | handed | forwarded | promised | mailed | loaned | posted | returned | slipped | wired

V_dat_pp  : given | lent | sold | offered | fed | passed | sent | rented | served | awarded | brought | handed | forwarded | promised | mailed | loaned | posted | returned | slipped | wired

V_dat_inf  : give | lend | sell | offer | feed | pass | send | rent | serve | award | bring | hand | forward | promise | mail | loan | post | return | slip | wire

S : NP_animate_nsubj_main V_main NP_animate_dobj_RC_modified | NP_animate_nsubj_main V_main NP_inanimate_dobj_RC_modified | NP_animate_nsubj_main V_dat NP_animate_iobj NP_inanimate_dobj_RC_modified | NP_animate_nsubj_main V_dat NP_inanimate_dobj_RC_modified PP_iobj | NP_animate_nsubj_main AUX V_dat_pp NP_inanimate_dobj_RC_modified | NP_animate_nsubj VP_cp | NP_animate_nsubj VP_external | NP_animate_nsubj_main_RC_modified VP_main_anim_subj | NP_animate_nsubj_main_RC_modified VP_main_anim_subj_unacc | NP_animate_nsubj_main_RC_modified VP_main_anim_subj_pass_dat | NP_inanimate_nsubj_main_RC_modified VP_main_inanim_subj | NP_animate_nsubj VP_cp

VP_cp : V_cp_taking C S

V_main : V_unacc | V_trans_omissible | V_trans_not_omissible

NP_animate_dobj_RC_modified : NP_animate_dobj_RC Rel_pron VP_RC_theme | NP_animate_dobj_RC Rel_pron VP_RC_agent | NP_animate_dobj_RC Rel_pron VP_RC_unacc_theme | NP_animate_dobj_RC Rel_pron VP_RC_pass_recipient

NP_inanimate_dobj_RC_modified : NP_inanimate_dobj Rel_pron VP_RC_theme | NP_inanimate_dobj Rel_pron VP_dat_RC_theme | NP_inanimate_dobj Rel_pron NP_animate_nsubj V_dat PP_iobj | NP_inanimate_dobj Rel_pron VP_RC_unacc_theme | NP_inanimate_dobj Rel_pron VP_RC_pass_theme

NP_animate_nsubj_main_RC_modified : NP_animate_nsubj_main Rel_pron VP_RC_agent | NP_animate_nsubj_main Rel_pron VP_RC_unacc_theme | NP_animate_nsubj_main Rel_pron VP_RC_pass_recipient | NP_animate_nsubj_main Rel_pron VP_RC_object_extracted_theme

NP_inanimate_nsubj_main_RC_modified : NP_inanimate_nsubj_main Rel_pron VP_RC_inanimate_subj_extracted_theme | NP_inanimate_nsubj_main Rel_pron VP_RC_object_extracted_theme | NP_inanimate_nsubj_main Rel_pron VP_dat_RC_theme | NP_inanimate_nsubj_main Rel_pron NP_animate_nsubj V_dat PP_iobj

VP_RC_inanimate_subj_extracted_theme : V_unacc | AUX V_trans_not_omissible_pp | AUX V_trans_not_omissible_pp BY NP_animate_nsubj | AUX V_trans_omissible_pp | AUX V_trans_omissible_pp BY NP_animate_nsubj | AUX V_unacc_pp | AUX V_unacc_pp BY NP_animate_nsubj | AUX V_dat_pp PP_iobj | AUX V_dat_pp PP_iobj BY NP_animate_nsubj

VP_RC_object_extracted_theme : NP_animate_nsubj V_unacc | NP_animate_nsubj V_trans_omissible | NP_animate_nsubj V_trans_not_omissible

VP_RC_theme : NP_animate_nsubj V_unacc | NP_animate_nsubj V_trans_omissible | NP_animate_nsubj V_trans_not_omissible

VP_dat_RC_theme : NP_animate_nsubj V_dat NP_animate_iobj

NP_animate_nsubj_main : N_prop_nsubj | Det N_common_animate_nsubj | Det N_common_animate_nsubj PP_loc

VP_RC_unacc_theme : V_unacc

VP_RC_pass_recipient : AUX V_dat_pp NP_inanimate_dobj | AUX V_dat_pp NP_inanimate_dobj BY NP_animate_nsubj

VP_RC_pass_theme : AUX V_trans_not_omissible_pp | AUX V_trans_not_omissible_pp BY NP_animate_nsubj | AUX V_trans_omissible_pp | AUX V_trans_omissible_pp BY NP_animate_nsubj | AUX V_unacc_pp | AUX V_unacc_pp BY NP_animate_nsubj | AUX V_dat_pp PP_iobj | AUX V_dat_pp PP_iobj BY NP_animate_nsubj

VP_RC_agent : V_unerg | V_unacc NP_dobj | V_trans_omissible | V_trans_omissible NP_dobj | V_trans_not_omissible NP_dobj | V_inf_taking INF V_inf | V_dat NP_inanimate_dobj PP_iobj | V_dat NP_animate_iobj NP_inanimate_dobj | V_cp_taking C C_internal

NP_animate_nsubj : N_prop_nsubj | Det N_common_animate_nsubj | Det N_common_animate_nsubj PP_loc

PP_iobj : P_iobj NP_animate_iobj | P_iobj NP_animate_iobj

NP_animate_iobj : Det N_common_animate_iobj | N_prop_iobj

NP_animate_dobj_RC : Det N_common_animate_dobj

NP_inanimate_dobj : Det N_common_inanimate_dobj | Det N_common_inanimate_dobj PP_loc

NP_inanimate_dobj_noPP : Det N_common_inanimate_dobj

C_internal : NP_animate_nsubj VP_external | VP_internal | NP_inanimate_nsubjpass VP_passive | NP_animate_nsubjpass VP_passive_dat

VP_external : V_unerg | V_unacc NP_dobj | V_trans_omissible | V_trans_omissible NP_dobj | V_trans_not_omissible NP_dobj | V_inf_taking INF V_inf | V_dat NP_inanimate_dobj PP_iobj | V_dat NP_animate_iobj NP_inanimate_dobj

VP_internal : NP_unacc_subj V_unacc

NP_dobj : NP_inanimate_dobj | NP_animate_dobj

NP_unacc_subj : NP_inanimate_dobj_noPP | NP_animate_dobj_noPP

NP_animate_dobj_noPP : Det N_common_animate_dobj | N_prop_dobj

NP_animate_dobj : Det N_common_animate_dobj | Det N_common_animate_dobj PP_loc | N_prop_dobj

NP_animate_nsubjpass : Det N_common_animate_nsubjpass | N_prop_nsubjpass

NP_inanimate_nsubjpass : Det N_common_inanimate_nsubjpass

VP_passive : AUX V_trans_not_omissible_pp | AUX V_trans_not_omissible_pp BY NP_animate_nsubj | AUX V_trans_omissible_pp | AUX V_trans_omissible_pp BY NP_animate_nsubj | AUX V_unacc_pp | AUX V_unacc_pp BY NP_animate_nsubj | AUX V_dat_pp PP_iobj | AUX V_dat_pp PP_iobj BY NP_animate_nsubj

VP_passive_dat : AUX V_dat_pp NP_inanimate_dobj | AUX V_dat_pp NP_inanimate_dobj BY NP_animate_nsubj

NP_on : Det N_on PP_loc | Det N_on

NP_in : Det N_in PP_loc | Det N_in

NP_beside : Det N_beside PP_loc | Det N_beside

PP_loc : P_on NP_on | P_in NP_in | P_beside NP_beside

PP_iobj : P_iobj NP_animate_iobj
```

I would like you to derive a sentence using each of the following derivation trees:

1.
```
(S
  (NP_animate_nsubj (Det) (N_common_animate_nsubj))
  (VP_external (V_trans_not_omissible) (NP_dobj (NP_animate_dobj (Det) (N_common_animate_dobj)))))
```

2.
```
(S
  (NP_animate_nsubj (Det) (N_common_animate_nsubj) (PP_loc (P_in) (NP_in (Det) (N_in))))
  (VP_external (V_trans_not_omissible) (NP_dobj (NP_animate_dobj (Det) (N_common_animate_dobj))))
)
```

3.
```
(S
  (NP_animate_nsubj_main_RC_modified
    (NP_animate_nsubj_main (Det) (N_common_animate_nsubj))
    (Rel_pron)
    (VP_RC_agent (V_unacc)))
  (VP_external
    (V_trans_not_omissible)
    (NP_dobj
      (NP_animate_dobj (Det) (N_common_animate_dobj)))))
```

4.
```
(S
  (NP_animate_nsubj_main_RC_modified
    (NP_animate_nsubj_main
      (Det) (N_common_animate_nsubj))
    (Rel_pron)
    (VP_RC_agent
      (NP_animate_nsubj
        (Det) (N_common_animate_nsubj))
      (V_trans_omissible)))
  (V_main)
  (NP_animate_dobj
    (Det) (N_common_animate_dobj)))
```

5.
```
(S
  (NP_animate_nsubj_main_RC_modified
    (NP_animate_nsubj_main (Det) (N_common_animate_nsubj))
    (Rel_pron)
    (VP_RC_agent
      (V_trans_not_omissible)
      (NP_dobj
        (NP_inanimate_dobj_RC_modified
          (NP_inanimate_dobj (Det) (N_common_inanimate_dobj))
          (Rel_pron)
          (VP_RC_pass_theme (AUX) (V_unacc_pp))))))
  (VP_main_anim_subj
    (VP_external
      (V_trans_not_omissible)
      (NP_dobj (NP_animate_dobj (Det) (N_common_animate_dobj))))))
```

6.
```
(S
  (NP_animate_nsubj_main_RC_modified
    (NP_animate_nsubj_main
      (Det)
      (N_common_animate_nsubj))
    (Rel_pron)
    (VP_RC_object_extracted_theme
      (NP_animate_nsubj_main_RC_modified
        (NP_animate_nsubj_main
          (Det)
          (N_common_animate_nsubj))
        (Rel_pron)
        (VP_RC_object_extracted_theme
          (NP_animate_nsubj_main
            (Det)
            (N_common_animate_nsubj))
          (V_trans_not_omissible)))
      (V_trans_not_omissible)))
  (VP_main_anim_subj
    (V_trans_not_omissible)
    (NP_dobj
      (NP_animate_dobj
        (Det)
        (N_common_animate_dobj)))))
```

I would like you to repeat this process in five sets. Within the same set, make sure to:
- use the same main subject, object and verb throughout
- make all embedded subjects AND verbs *DIFFERENT*

Output just the numbered sentences without any extra information.
    """
    prompt = get_prompt(
        number=number_description,
        tense=tense_description,
        theme=theme_description,
        n=1,
        special_prompt=special_prompt
    )

    if print_prompt:
        print("Generated prompt:")
        print("-" * 50)
        print(prompt)
        print("-" * 50)

    response = gpt4_response(
        prompt=prompt,
        model=DEFAULT_MODEL,
        frequency_penalty=0.1,
        presence_penalty=0.
    )

    print("\nGenerated response:")
    print("-" * 50)
    print(response)
    print("-" * 50)


def generate_speech(
    sentences: Union[str, List[str]],
    sentence_type: str = "relative",  # relative, cleft, or pronouns
    voice: str = "alloy",
    model: str = "tts-1"
) -> List[Path]:
    """
    Generate speech audio files for one or multiple sentences.

    Args:
        sentences: Single sentence string or list of sentences
        sentence_type: Type of sentences (relative, cleft, or pronouns)
        voice: OpenAI TTS voice to use
        model: OpenAI TTS model to use

    Returns:
        List of paths to generated audio files
    """
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Convert single string to list for uniform processing
    if isinstance(sentences, str):
        sentences = [sentences]

    # Create subdirectory for sentence type if it doesn't exist
    output_dir = AUDIO_DIR / sentence_type
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_files = []

    for sentence in sentences:
        # Sanitize the sentence for filename
        safe_sentence = sanitize_filename(sentence)
        safe_sentence = safe_sentence.replace(" ", "_")

        # Create full file path
        speech_file_path = output_dir / f"{safe_sentence}_{voice}.wav"

        # Skip if file already exists
        if speech_file_path.exists():
            print(f"File already exists: {speech_file_path}")
            generated_files.append(speech_file_path)
            continue

        try:
            # Generate speech
            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=sentence  # Use original sentence for audio generation
            )

            # Save the audio file
            response.stream_to_file(str(speech_file_path))
            generated_files.append(speech_file_path)
            print(f"Generated: {speech_file_path}")

        except Exception as e:
            print(f"Error generating audio for sentence: {sentence}")
            print(f"Error: {str(e)}")
            continue

    return generated_files


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a filename.

    Args:
        filename: String to sanitize

    Returns:
        Sanitized string safe for use as filename
    """
    # Remove invalid filename characters and limit length
    sanitized = re.sub(r'[\\/*?:"<>|\n\r\t]', "", filename)
    sanitized = sanitized.replace("'", "")  # Remove apostrophes
    return sanitized[:200]  # Limit filename length


import pandas as pd
import random
import re
from pathlib import Path


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


def generate_enhanced_csvs(sentences_dir: Path = SENTENCES_DIR / "V2"):
    """
    Generate CSV files with basic sentence information and file metadata.
    Added set_number and sentence_number columns, improved structure matching,
    and ensures themes are grouped together.
    """
    categories = [d for d in sentences_dir.iterdir() if d.is_dir()]

    for category in categories:
        category_name = category.name
        all_sentences = []

        # Read all txt files in the category directory
        txt_files = sorted(list(category.glob('*.txt')))

        set_number = 1

        for txt_file in txt_files:
            # Extract theme, numerosity, and tense from filename
            file_parts = txt_file.stem.split('_')
            if len(file_parts) >= 3:
                theme, numerosity, tense = file_parts[:3]
            else:
                theme = file_parts[0] if len(file_parts) > 0 else 'unknown'
                numerosity = file_parts[1] if len(file_parts) > 1 else 'unknown'
                tense = file_parts[2] if len(file_parts) > 2 else 'unknown'
 
            with open(txt_file, 'r') as f:
                content = f.read().strip()
                sentences = [s.strip() for s in content.split('\n') if s.strip()]
                
                sentence_number = 1
                
                for s in sentences:
                    if match := re.match(r'(\d+)([a-d]?)\.?\s*(.*)', s):
                        number, variation, text = match.groups()
                        # Maintain original labeling (a, b, c, d)
                        variation = variation if variation else 'a'
                        
                        # Determine the structure properly based on number and variation
                        structure_types = {
                            '1': 'baseline',
                            '2': 'control', 
                            '3': 'standard_subject',
                            '4': 'standard_object',
                            '5': 'nested_subject',
                            '6': 'nested_object'
                        }
                        
                        structure_base = structure_types.get(number, f"unknown_type_{number}")
                        structure = f"{structure_base}_{variation}"

                        sentence_info = {
                            'set_number': set_number,
                            'sentence_number': sentence_number,
                            'theme': theme,
                            'numerosity': numerosity,
                            'tense': tense,
                            'sentence': text.strip(),
                            'word_count': len(text.strip().split()),
                            'structure': structure,
                        }
                        all_sentences.append(sentence_info)
                        sentence_number += 1

            set_number += 1

        if not all_sentences:
            print(f"No sentences found in {category}")
            continue

        # Create ordered DataFrame - sort by theme first, 
        # then set_number, then sentence_number
        df_ordered = pd.DataFrame(all_sentences)
        df_ordered = df_ordered.sort_values(
            by=['theme', 'set_number', 'sentence_number']
        ).reset_index(drop=True)

        # Save ordered CSV
        ordered_path = Path(
            category.parent / 'processed' / f"{category_name}_ordered.csv"
        )
        df_ordered.to_csv(ordered_path, index=False)

        # Create shuffled version by reading
        # the ordered CSV and shuffling all rows
        df_shuffled = pd.read_csv(ordered_path)
        df_shuffled = df_shuffled.sample(frac=1).reset_index(drop=True)

        # Save shuffled CSV
        shuffled_path = Path(
            category.parent / 'processed' / f"{category_name}_shuffled.csv"
        )
        df_shuffled.to_csv(shuffled_path, index=False)

        print(f"Generated CSV files for {category_name}:")
        print(f"- Ordered: {ordered_path}")
        print(f"- Shuffled: {shuffled_path}")


def estimate_reading_time(text, words_per_minute=250):
    """
    Estimate the reading time of a sentence.

    Parameters:
    text (str): The sentence for which to estimate reading time.
    words_per_minute (int): Average reading speed in words per minute (default is 250).

    Returns:
    float: Estimated reading time in seconds.
    """
    word_count = len(text.split())
    reading_time_minutes = word_count / words_per_minute
    reading_time_seconds = reading_time_minutes * 60
    return reading_time_seconds


if __name__ == "__main__":
    # Single sentence
    single_sentence = "The cat sat on the mat."
    generate_speech(single_sentence, sentence_type="relative")

    # Multiple sentences
    sentences = [
        "The dog chased the ball.",
        "The bird flew in the sky.",
        "The fish swam in the pond."
    ]
    generate_speech(sentences, sentence_type="cleft")
