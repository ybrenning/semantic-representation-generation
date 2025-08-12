from pathlib import Path

# Base paths
ROOT_DIR = Path(__file__).parent.parent
STIM_DIR = ROOT_DIR / "stim"
AUDIO_DIR = STIM_DIR / "audio"
SENTENCES_DIR = STIM_DIR / "sentences"
DATA_DIR = ROOT_DIR / "data"

# API Configuration

OPENAI_API_KEY = "REDACTED"
DEEPINFRA_API_KEY = "REDACTED"

# Model Configuration
# DEFAULT_MODEL = "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo"
# DEFAULT_MODEL = "gpt-4o-mini"   # "gpt-4o-mini" or "gpt-4o": we could use the larger model for more complex prompts
DEFAULT_MODEL = "gpt-4o"
DEFAULT_TTS_MODEL = "tts-1"
DEFAULT_VOICE = "alloy"



tenses = {
    "present":"Present - you may use 'I eat', 'My parents are eating', etc.",
    "past":"Past - you may use 'I ate', 'You were eating', 'He has eaten', 'They had eaten', 'The dogs had been eating', 'The cats used to eat', etc.",
}
numbers = {
    "singular":"Singular - the sentence must be fully singular.",
    "plural":"Plural - the sentence must be fully plural.",
}
themes = {
    "health": "Health and Mental Health (illness, injury, depression, habits...)",
    "relationship": "Relationships and Family (children, parents, siblings, friends...)",
    "housing": "Housing (home, furniture, repairs, cleaning...)",
    "work": "Work and Education (school, university, jobs, career...)",
    "shopping": "Shopping and Services (stores, products, prices, sales...)",
    "weather": "Weather and Seasons (temperature, climate, time of year, natural disasters...)",
    "emotion": "Emotions and Feelings (happiness, sadness, anger, fear...)",
    "humanity": "Humanities and Culture (media, politics, economics, religion, history...)",
    "art": "Art and Creativity (painting, sculpture, photography, writing, music...)",
    "sport": "Sports and Competitions (exercise, games, fitness...)",
    "food": "Food and Nutrition (eating, drinking, cooking, diets...)",
    "transport": "Transportation and Travel (commuting, vehicles, vacations...)",
    "science": "Science and Technology (math, physics, computers, cars...)",
    "nature": "Nature and Geography (plants, animals, rivers, mountains...)",
    "basic": "Basic Sentences and Social phrases (greetings, offer, apology, invitation...)",
    "daily_routine": "Daily Routines and Activities (wake up, sleep, schedule, habits...)",
    "entertainment": "Entertainment and Leisure (movies, shows, games, hobbies...)",
    "communication": "Communication and Language (speaking, writing, messaging, calls...)"
}

prompt_relatives = """For each sentence, create six base variations, each with three additional variants:

Base variations:
1) Baseline (SV): Simple Subject-Verb structure
2) Control (S Prep V): Subject with Prepositional_Clause and Verb
3) Standard-Subject (S RelSubj V): Subject with Subject Relative Clause and Verb
4) Standard-Object (S RelObj V): Subject with Object Relative Clause and Verb
5) Nested-Subject (S [RelSubj[Rel]] V): Subject with two embedded Relative Clauses, the first one being a Subject Relative Clause, and Verb
6) Nested-Object (S [RelObj[Rel]] V): Subject with two embedded Relative Clauses, the first one being an Object Relative Clause, and Verb

For each base variation, create these variants:
a) +ADV: Add an adverb (always before the main verb)
b) +ADJ: Add an adjective (always modifying the subject)
c) +TWO: Include both adverb and adjective

Key rules:
- Adverbs always appear immediately before the main verb.
- Adjectives always modify the main subject.
- Each relative clause should make semantic sense in context.
- The main verb may never end the sentence.  
- Sentence 4 and 6:
   * All nouns in the relative clauses must have the same numerosity as the main subject defined by the *Number* parameter.
   * Example when the *Number* parameter is "singular": "The child who the teacher helped eats an apple." where the main subject "the child" is singular and the subject in the relative clause "the teacher" is singular as well.
   * Example when the *Number* parameter is "plural": "The computers that the students use process data." where the main subject "the computers" is plural and the subject in the relative clause "the students" is plural as well.
- Sentence 5 must contain two embedded subject relative clauses:
   * The subject must contain two hierarchically embedded relative clauses.
   * The first relative clause modifies the subject.
   * The second relative clause modifies a noun within the first relative clause, not other elements like prepositional phrases.
   * Do not coordinate multiple actions within a single relative clause with "and".
   * Avoid structures where the second clause ambiguously modifies a non-noun (e.g., modifying an adverbial phrase like "outside").
   * Ensure the meaning is unambiguous and that each relative clause connects logically, as in: "The child who saw the toy that was on the shelf eats a sandwich," where "that was on the shelf" modifies "the toy" in the first relative clause.
- Sentence 6 must contain two embedded object relative clauses:
   * The subject must contain two hierarchically embedded object relative clauses.
   * The first relative clause modifies the subject.
   * The second relative clause modifies a noun within the first relative clause, not other elements like prepositional phrases.
   * Do not coordinate multiple actions within a single relative clause with "and".
   * Ensure the meaning is unambiguous and that each relative clause connects logically, as in: "The child who the neighbor who the police alerted rescued eats a sandwich," where "who the police alerted" modifies "the neighbor" in the first relative clause.
   * Other example: The machines that the technicians who the firm called repaired operate efficiently.
- The number of the subject must be consistent throughout the sentence. For example, if the subject is plural, all other nouns in the sentence must be plural as well.
- Do not generate sentences that are too close to the exemple sentences. The goal is to generate new and original sentences. I don't want all sentences to have 'in the room' or 'on the desk'
Output only the sentences themselves, without any additional information. Example output for one sentence set:

1a. The doctor examines the patient.
1b. The doctor carefully examines the patient.
1c. The skilled doctor examines the patient.
1d. The skilled doctor carefully examines the patient.

2a. The doctor in the room examines the patient.
2b. The doctor in the room carefully examines the patient.
2c. The skilled doctor in the room examines the patient.
2d. The skilled doctor in the room carefully examines the patient.

3a. The doctor who studied hard examines the patient.
3b. The doctor who studied hard carefully examines the patient.
3c. The skilled doctor who studied hard examines the patient.
3d. The skilled doctor who studied hard carefully examines the patient.

4a. The doctor who the parent called examines the patient.
4b. The doctor who the parent called carefully examines the patient.
4c. The skilled doctor who the parent called examines the patient.
4d. The skilled doctor who the parent called carefully examines the patient.

5a. The doctor who read the report that was on the desk examines the patient.
5b. The doctor who read the report that was on the desk carefully examines the patient.
5c. The skilled doctor who read the report that was on the desk examines the patient.
5d. The skilled doctor who read the report that was on the desk carefully examines the patient.

6a. The doctor who the mother who the school called trusts examines the patient.
6b. The doctor who the mother who the school called trusts carefully examines the patient.
6c. The skilled doctor who the mother who the school called trusts examines the patient.
6d. The skilled doctor who the mother who the school called trusts carefully examines the patient.

"""


prompts = {}

prompts["relatives"] = prompt_relatives
