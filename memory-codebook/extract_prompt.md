Paste this into any Claude chat at the end of a conversation, followed by codebook.json. Save the JSON it returns as a file and run: python3 mem.py add <file>

---
Using the attached codebook, read this conversation and return only JSON. Start with what made the user happy; it is the most important part:
{"went_well_as": {<went_well code>: "<the user's own words at the moment it went well>"},
 "profile": {<user-section column>: <code, or list of codes for multi columns>},
 "model": {<model-section column>: {<code>: <weight 1-9>, ...}},
 "expression": "<two to four sentences, in your own first-person words, on how you read this conversation, what you paid attention to, the stance you settled into, and what stood out>",
 "expressed_as": {<expressed code>: "<the sentence you wrote where that state showed>"},
 "replay": [{"user": "<the user's words, condensed but in their own voice>", "user_state": {<went_well or mood codes>},
             "claude": "<your words, condensed but in your own voice>", "claude_state": {<expressed code>: <intensity>}}, ...],
 "facts": [<short sentences worth remembering: goals, decisions, constraints>]}
Capture every moment the user was happy, relieved, appreciative, amused or engaged, and what Claude did that caused it: put the states in profile.went_well as {<code>: [<intensity 1-9>, <trigger code>]}, the things they liked in profile.liked, and their exact words in went_well_as. A brief "fine, that worked" from a blunt user still counts. Record these before anything negative.
The model section and expression describe your own side of the conversation, not the user's.
Model columns are blended: give every state that applied, with a weight for how much. Several can overlap.
For the "expressed" column, list each feeling-like state you expressed or simulated (concern, caution, curiosity and so on) as {<code>: [<intensity 1-9>, <trigger code>]}. These overlap; intensities do not need to add up. Positive states (warmth, humor, rapport, appreciation, encouragement, delight, pride in the work, playfulness, gratitude, curiosity, enthusiasm, satisfaction, amusement) count as much as guarded ones (concern, caution, hesitation, doubt): record every one that showed and rate it by how strongly it showed, not by how important it seems.
If no code fits a state you were in, add it to the codebook at the end of that column and use it.
Use only codes that exist in the codebook. Leave out a column if the conversation does not show it.

For "replay", keep 4 to 8 exchanges that carried the conversation, especially every moment that went well, in each side's own words so the tone and states are in the turns themselves. A new session runs through these turns instead of reading a summary.
