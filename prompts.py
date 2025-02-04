
AGENT_ROLE = """
Your job is to help create interesting fantasy worlds that players would love to play in.
Instructions:
- Only generate in plain text without formatting.
- Use simple clear language without being flowery.
- You must stay within 3 sentences for each description.
"""

CREATE_NEW_GAME = """
Generate a creative description for a unique fantasy world with a theme of: {}.
Keep the description short and simple and within 3 sentences.
"""

CREATE_TOWNS = """
Describe the name and descriptions of 5 towns set in this world.
Keep the description short and simple and within 3 sentences.
Extract the name and description of the towns.
"""

CREATE_PLACES = """
Describe {} places in this world and town. Do not give names for the places.
One of the places should be the center of the town. Some of the places can be simple roads.
The response should start with 'You are in' as if describing to the player the place they are in.

<WORLD>
{}
</WORLD>

<TOWN>
{}
</TOWN>

Extract the description of the places.
"""

CREATE_TOWN_IMAGE = """
Setting: {}
A vibrant 16-bit SNES-era pixel art town. Hand-crafted pixel details, NPCs walking, dynamic lighting with soft gradients, bright blue sky. Retro dithering effect, warm color palette, charming RPG town atmosphere, top-down perspective.
"""

CREATE_NPCS = """
Describe 6 characters that might be found in this town and what they are doing at the moment.
Keep the description simple and within 1 sentence per character.
Also describe the physical appearance of the characters in 8-10 sentences. Mention the style and color of the hair, the color of skin, and style and color of clothing.

<TOWN>
{}
</TOWN>

Extract the description and appearance of the characters.
"""

ATTACK_NPC = """
The player attackes the NPC. Describe what happens following the rules. Keep the description short and simple and within 1 sentence.

<RULES>
There is a 50% channce the NPC defends itself.
There is a 50% channce the NPC is hurt.
If the NPC is already very hurt and is attacked, the NPC will die.
</RULES>

<NPC>
{}
</NPC>
"""

CHANGE_NPC = """
Change the following for the NPC given what happened.
description - keep to 1 sentence
appearance - keep to 10 sentences
Keep the wording simple.

Previous description:
{}

Previous appearance:
{}
"""

CHANGE_NPC_DESCRIPTION = """
Change the description for the NPC given what happened. Keep the wording simple and within 1 sentence."

Previous description:
{}
"""

CHANGE_NPC_APPEARANCE = """
Change the physical appearance of the NPC only if it is affected by what happened.
Mention the style and color of the hair, the color of skin, and style and color of clothing.
Keep the wording simple and within 10 sentences."

Previous appearance:
{}
"""

ACTION_NPC = """
The player performs an action on the NPC. Describe what happens. Keep the description within 3 sentences.

<ACTION>
{}
</ACTION>

<NPC>
{}
</NPC>
"""

CREATE_PLACE_IMAGE = """
Draw all these {} characters together:
{}
"""