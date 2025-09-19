# Prompts

The overall idea for all prompts is to constrain `gpt-4o` to a context-free grammar while generating sentences following the following six structures:

1) Baseline (SV): Simple Subject-Verb structure
2) Control (S Prep V): Subject with Prepositional_Clause and Verb
3) Standard-Subject (S RelSubj V): Subject with Subject Relative Clause and Verb
4) Standard-Object (S RelObj V): Subject with Object Relative Clause and Verb
5) Nested-Subject (S [RelSubj[Rel]] V): Subject with two embedded Relative Clauses, the first one being a Subject Relative Clause, and Verb
6) Nested-Object (S [RelObj[Rel]] V): Subject with two embedded Relative Clauses, the first one being an Object Relative Clause, and Verb

For example:

1. The doctor examines the patient.
2. The doctor in the room examines the patient.
3. The doctor who studied hard examines the patient.
4. The doctor who the parent called examines the patient.
5. The doctor who read the report that was on the desk examines the patient.
6. The doctor who the mother who the school called trusts examines the patient.
