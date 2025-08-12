# neurospin-new-protocol


## General description

This repository contains all the code for the sentence / audio generation for the upcoming MEG experiment.

Two sets of sentences are generated:

- Naturalistic, everyday life, non-controlled stimuli dataset. 
Code can be found at ntbk/natural_dataset.ipynb, and the resulting file is full.csv, which contains the 60K generated sentences.


- Controlled, syntacticly interesting and focused dataset.
Code can be found in src, and the resulting files are found in stim/sentences/*category*

## Running the code

The prompts used to generate the datasets can be found in config/config.py.

To do some testing, run ```python debug.py --category relatives```. It allows you to modify the prompts and see how it impacts the generation, directly in your terminal.

## In depth description

Both datasets have been generated doing a grid search through 3 dimensions: themes, tenses and plurality.

### Naturalistic dataset

For the naturalistic dataset, the prompt was to generate 20 sentences for a given combination, using simple yet diverse vocabulary.

### Controlled dataset

For the controlled dataset, depending on the category (relatives, cleft, pronouns), we generate N groups of sentences. We'll focus on relatives here as it's the only condition we'll keep for the first experiment.

Given a tense, a theme and a plurality, we generate for relatives:
5 groups of sentences:

1) Baseline (SV): Simple Subject-Verb structure
2) Control (S Prep V): Subject with Prepositional_Clause and Verb
3) Standard-Subject (S RelSubj V): Subject with Subject Relative Clause and Verb
4) Standard-Object (S RelObj V): Subject with Object Relative Clause and Verb
5) Nested (S Rel&Rel V): Subject with two embedded Relative Clauses and Verb

For each base variation, create these variants:
a) +ADV: Add an adverb (always before the main verb)
b) +ADJ: Add an adjective (always modifying the subject)
c) +TWO: Include both adverb and adjective

Which creates a group of 20 sentences for each combination.


### STIM dataset

The final dataset that will be used for the MEG experiment will be composed of the two datasets, filtered.

For the final dataset, we chose to keep a vocabulary of 500 words for the naturalistic dataset; which gives us around 1000 sentences.
We add the controlled dataset to it, which gives us 1600 sentences.
The sentences will then be turned into speech using the OpenAI API. 

To organize the sentences for the experiment, we decide to keep the same sentences for all subjects, to be able to perform across-subjects analyses. 

### STIM Presentation
In terms of presentation format, the sentences's audio will be played and the subject will be asked to press a button once he's comfortable repeating the sentence inside it's head. 

Typical trial:
0s: Sentence starts playing
2s: Sentence stops playing
3s: Subject pushes the button to communicate he is starting to repeat the sentence inside his head.
4.5s: Subject pushes the button again to communicate he finished repeating the sentence inside his head.
6.5s: Next sentence starts playing
etc...

On average, we consider a trial to be of approx ~10 seconds (with sentences ranging from 1.5s to 5s).
This gives us 10s * 1600 sentences ~ 4h30 minutes, which means approx 4 sessions. If we present each sentences twice, we could go to around 8 sessions.

### STIM organization

In terms of runs and sentences, we want the same sentences played for each subject.
However, we need to have a different order of sentences to not create some regularities between sentences presented.

We decided to blend together all of the sentences from the two datasets, and divide them into runs of 10/15 minutes, by groups of 80 sentences.

All the sentences will be randomly shuffed, and we might add some constraints in the shuffling to make sure to have:
- the 3 first sentences to be naturalistic ones: we might remove them since accounting them as "training".
- sentences with more than 10 words shouldn't appear in a row. 

This gives us files to track the experiment:
- In one folder: stim/audio, we have all the audio files, with a naming convention for each dataset:
    - Naturalistic: sentence_id.wav
    - Controlled: tense_theme_plurality_variation.wav
- In another folder: stim/sentences/clean, we have:
    - a csv file with all the sentences: final.csv, and two columns: one called audio_filename, to link it to the audio file, and another one called block_number_subX which links it to the block it belongs for a given subject.
    - the naturalistic.csv file which contains the inital 32K sentences.
    - the controlled sentences dataset in the controlled.csv file.
    - a notebook that was used to generate all the given files, to track how it was done and reproduce it if needed.





