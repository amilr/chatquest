import os, requests, random
from io import BytesIO
from typing import Dict, List
from enum import Enum
from pprint import pprint
import database as db
import prompts, metaprompts
import mapgenerator as mapg
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from client_factory import create_client

import imaging
from world import World, Town, Place, NPC, Point, TownList, PlaceList, NPCList, GenImage

class Move(Enum):
    North = 1
    South = 2
    East = 3
    West = 4

# parameters
load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
AI_PROVIDER = os.getenv('AI_PROVIDER', 'groq')
METAPROMPTER_PROVIDER = os.getenv('METAPROMPTER_PROVIDER', AI_PROVIDER)

world_dict = {}

HELP_TEXT = """I'm here to create a game.
/newgame <description> to begin a game
/look to look around
/who to find characters
/n /s /e /w to move
/1 /2 /... <action> to interact with characters
/talk <message> to talk to the selected character (use /1 /2 /etc first to select a character)
"""

def register_game_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if "chat_ids" not in context.bot_data:
        context.bot_data["chat_ids"] = set()
    
    if chat_id not in context.bot_data["chat_ids"]:
        print("New chat ID detected")
        context.bot_data["chat_ids"].add(chat_id)
        
        chat_id_str = str(chat_id)
        game_session_id = db.get_game_session(chat_id)
        
        if game_session_id:
            print(f"Found existing game session in DB: {game_session_id}")
        else:
            game_session_id = db.create_game_session(chat_id)
            print(f"Created new game session in DB: {game_session_id}")

        messages = db.get_message_history(game_session_id)
        game_session = {
            'id': game_session_id,
            'history': messages
        }
        context.bot_data["chat_id:" + chat_id_str] = game_session

    else:
        game_session = context.bot_data["chat_id:" + str(chat_id)]
        game_session_id = game_session['id']
        print(f"Found game session in context: {game_session_id}")

    return game_session

def store_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game_session = register_game_session(update, context)
    user = update.effective_user
    username = user.username
    message = update.message.text
    
    game_session['history'].append({'sender': username, 'message': message})
    sequence = len(game_session['history'])
    
    #db.store_message_to_db(game_session['id'], sequence, username, message)
    
    print(game_session['id'])
    print(game_session['history'])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_message(update, context)
    await send_message(update, context, HELP_TEXT)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_message(update, context)
    await send_message(update, context, HELP_TEXT)

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE, image: bytes, caption: str):
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image, caption=caption)

async def display_none_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_message(update, context, "No game in progress. Use /newgame <description> to start a game.")

async def display_creating_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_message(update, context, "Please wait while I create a new world for you.")

def new_world(update: Update):
    chat_id = update.effective_chat.id
    new_world = World()
    world_dict[chat_id] = new_world
    print(f'Created world: {chat_id}')
    return new_world

def get_world(update: Update):
    chat_id = update.effective_chat.id
    
    if chat_id in world_dict:
        print(f'Using world: {chat_id}')
        return world_dict[chat_id]
    
    new_world = World()
    world_dict[chat_id] = new_world
    print(f'Created world: {chat_id}')
    return new_world

def get_npcs_text(npc_list: List[NPC]) -> tuple[int, str]:
    text = ""
    ctr = 0
    for npc in npc_list:
        ctr += 1
        text += "{}. {} {}\n".format(ctr, npc.description, npc.appearance)
    return ctr, text

def get_npcs_image(metaprompter, npc_list) -> bytes:
    num, npcs_text = get_npcs_text(npc_list)
    meta_prompt = metaprompts.CHARACTERS.format(npcs_text)

    metaprompter.reset()
    metaprompter.prompt(meta_prompt)
    img_prompt = metaprompter.get_response()
    
    image = imaging.generate_image_dynamic(img_prompt, cells = num)
    return image

def print_map(grid):
    for row in grid:
        print(str(row).replace("''", "'   '"))

def render_map(grid, player_location: Point) -> str:
    """Return a string representation of the map using colored emoji."""
    # Colors for up to seven different towns, cycle if more
    colors = [
        "🟥", "🟦", "🟩", "🟨", "🟪", "🟧", "🟫"
    ]
    empty = "⬜"
    player_dot = "🔴"

    lines = []
    for y, row in enumerate(grid, start=1):
        line = ""
        for x, cell in enumerate(row, start=1):
            if x == player_location.x and y == player_location.y:
                line += player_dot
            elif cell == "":
                line += empty
            else:
                town_index = int(cell.split(":")[0]) - 1
                line += colors[town_index % len(colors)]
        lines.append(line)
    return "\n".join(lines)

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global world_dict

    world = new_world(update)

    world.ai = create_client(AI_PROVIDER)
    world.metaprompter = create_client(METAPROMPTER_PROVIDER)

    world.set_creating()

    store_message(update, context)

    await display_creating_status(update, context)

    # create world
    world.ai.init_chat()

    instruction = prompts.CREATE_NEW_GAME.format(update.message.text.replace('/newgame ', ''))
    world.ai.prompt(instruction)
    
    world.description = world.ai.get_response()
    print(world.description)

    # create world map
    grid, town_places_count, start_location = mapg.generate_map(3, 2, 3)

    print_map(grid)
    pprint(town_places_count)
    pprint(start_location)

    world.map = grid
    world.location = Point(start_location[0], start_location[1])

    # create towns
    await send_message(update, context, "Creating towns ...")
    world.ai.prompt(prompts.CREATE_TOWNS.format(len(town_places_count)))
    world.towns = world.ai.get_json_response(type = TownList).items

    # create places in towns
    await send_message(update, context, "Creating places ...")
    town_count = 1
    for town in world.towns:
        pprint(town)
        
        world.ai.init_chat()
        
        instruction = prompts.CREATE_PLACES.format(town_places_count[town_count], world.description, town.description)
        world.ai.prompt(instruction)

        places = world.ai.get_json_response(type = PlaceList).items
        place_count = 1
        for place in places:
            pprint(place)
            place_key = "{}:{}".format(town_count, place_count)
            world.places_dict[place_key] = place
            place_count += 1

        town_count += 1

    pprint(world.places_dict)

    # create town images
    town_count = 1
    await send_message(update, context, "Creating pictures ...")
    for town in world.towns:
        meta_prompt = metaprompts.TOWN_IMAGE.format(town.description)
        world.metaprompter.reset()
        world.metaprompter.prompt(meta_prompt)
        img_prompt = world.metaprompter.get_response()

        image_data = imaging.generate_image_large(img_prompt)
        world.towns_images.append(image_data)
        if image_data is None:
            print("No image for {}".format(town.name))
        else:
            print("Created image for {}".format(town.name))
        town_count += 1

    # create NPCs
    await send_message(update, context, "Creating characters ...")
    world.init_npc_dict()
    for idx, town in enumerate(world.towns):
        town_idx = idx + 1
        
        world.ai.init_chat()
        
        instruction = prompts.CREATE_NPCS.format(town_places_count[town_idx], town.description)
        world.ai.prompt(instruction)

        npc_list = world.ai.get_json_response(type = NPCList).items
        pprint(npc_list)
        
        place_keys = [key for key in world.places_dict.keys() if key.startswith(f"{town_idx}:")]
        for npc in npc_list:
            selected_place_key = random.choice(place_keys)
            world.npcs_dict[selected_place_key].append(npc)
            pprint("{} - adding: {}".format(selected_place_key, npc.description))

    # initialize empty image objects for the NPCs in each place
    for place_key, npc_list in world.npcs_dict.items():
        if len(npc_list) == 0:
            world.places_npc_images_dict[place_key] = None
        else:
            world.places_npc_images_dict[place_key] = GenImage(data=bytes(), dirty=True)

    await send_message(update, context, world.description)
    
    town_index, town, place_key, place = world.get_current_place()
    world.current_town = town
    await describe_scene(update, context, town_index, town, place_key, place, True)

    world.set_started()

async def describe_scene(update: Update, context: ContextTypes.DEFAULT_TYPE, town_index, town, place_key, place, has_entered_new_town):
    global world_dict

    world = get_world(update)

    print_map(world.map)
    print("{} -> {}".format(world.location, world.get_place_key()))

    scene = None
    if has_entered_new_town:
        scene = "You have entered {0}. {1}".format(town.name, town.description)
        if world.towns_images[town_index] is not None:
            img_data = world.towns_images[town_index]
            print("Start - display image for town {}: {} bytes".format(town_index, len(img_data)))
            await send_image(update, context, world.towns_images[town_index], scene)
            scene = ""
            print("End - display image for town {}".format(town_index))
    else:
        scene = "You are in {0}.".format(town.name)

    scene += "\n\n{0}".format(place.description)

    await send_message(update, context, scene)

async def move(update: Update, context: ContextTypes.DEFAULT_TYPE, move):
    global world_dict

    world = get_world(update)

    if world.not_started():
        await display_none_status(update, context)
        return
    elif world.creating():
        await display_creating_status(update, context)
        return

    new_location = None
    if move == str(Move.North):
        new_location = Point(world.location.x, world.location.y - 1)
    elif move == str(Move.South):
        new_location = Point(world.location.x, world.location.y + 1)
    elif move == str(Move.East):
        new_location = Point(world.location.x + 1, world.location.y)
    elif move == str(Move.West):
        new_location = Point(world.location.x - 1, world.location.y)

    if not world.can_move(new_location):
        await update.message.reply_text("You  cannot go that way.")
    else:
        world.location = new_location
        world.ai.init_chat()

    town_index, town, place_key, place = world.get_current_place()
    has_entered_new_town = (world.current_town != town)
    world.current_town = town
    world.selected_npc_index = 0

    await describe_scene(update, context, town_index, town, place_key, place, has_entered_new_town)
    
async def go_north(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await move(update, context, str(Move.North))

async def go_south(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await move(update, context, str(Move.South))

async def go_east(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await move(update, context, str(Move.East))

async def go_west(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await move(update, context, str(Move.West))

async def look(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global world_dict

    world = get_world(update)

    if world.not_started():
        await display_none_status(update, context)
        return
    elif world.creating():
        await display_creating_status(update, context)
        return

    town_index, town, place_key, place = world.get_current_place()
    await describe_scene(update, context, town_index, town, place_key, place, False)

async def who(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global world_dict

    world = get_world(update)

    if world.not_started():
        await display_none_status(update, context)
        return
    elif world.creating():
        await display_creating_status(update, context)
        return

    npcs = world.get_npcs()

    if len(npcs) == 0:
        await send_message(update, context, "There is no one here.")
    else:
        npc_text = ""
        for idx, npc in enumerate(npcs):
            npc_text += "[{}] {}\n\n".format((idx+1), npc.description)

        gen_image = world.get_place_image()
        if gen_image.dirty:
            # regenerate image
            gen_image.data = get_npcs_image(world.ai, world.get_npcs())
            gen_image.dirty = False

        await send_image(update, context, gen_image.data, npc_text)

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global world_dict

    world = get_world(update)

    target = update.message.text.replace('/attack ', '').strip()

    if target.isdigit():
        target_npc = world.get_npc(int(target))
        print(f"Attack target: {target}")

        if target_npc is None:
            await send_message(update, context, "Invalid target.")
        else:
            instruction = prompts.ATTACK_NPC.format(target_npc.description)
            world.ai.prompt(instruction)
            
            action_result = world.ai.get_response()
            print(f"Action result: {action_result}")
            await send_message(update, context, action_result)

            # update NPC description
            world.ai.prompt(prompts.CHANGE_NPC.format(target_npc.description, target_npc.appearance))
            updated_npc = world.ai.get_json_response(type = NPC)
            target_npc.description = updated_npc.description
            target_npc.appearance = updated_npc.appearance
            print(f"Changed NPC: {target_npc}")

            # update place image
            world.places_npc_images_dict[world.get_place_key()].dirty = True


async def show_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the world map as a colored grid with the player's position."""
    global world_dict

    world = get_world(update)

    if world.not_started():
        await display_none_status(update, context)
        return
    elif world.creating():
        await display_creating_status(update, context)
        return

    map_text = render_map(world.map, world.location)
    await send_message(update, context, map_text)

# Actions
async def act(update: Update, context: ContextTypes.DEFAULT_TYPE, target: int, action: str):
    global world_dict

    world = get_world(update)

    target_npc = world.get_npc(target)
    print(f"Action target: {target}")

    if target_npc is None:
        await send_message(update, context, "Invalid target.")
    else:
        instruction = prompts.ACTION_NPC.format(action, target_npc.description)
        world.ai.prompt(instruction)
        
        action_result = world.ai.get_response()
        print(f"Action result: {action_result}")
        await send_message(update, context, action_result)

        # update NPC description
        world.ai.prompt(prompts.CHANGE_NPC_DESCRIPTION.format(target_npc.description))
        updated_description = world.ai.get_response()
        target_npc.description = updated_description

        world.ai.prompt(prompts.CHANGE_NPC_APPEARANCE.format(target_npc.appearance))
        updated_appearance = world.ai.get_response()
        target_npc.appearance = updated_appearance
        
        print(f"Changed NPC: {target_npc}")

        # update place image
        world.places_npc_images_dict[world.get_place_key()].dirty = True

def get_action(update: Update, selected_npc_index: int) -> str:
    global world_dict

    world = get_world(update)
    world.selected_npc_index = selected_npc_index

    parts = update.message.text.split(' ', 1)
    if len(parts) == 1:
        return None
    else:
        return parts[1]

async def act_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = get_action(update, 1)
    if action is not None:
        await act(update, context, 1, action)

async def act_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = get_action(update, 2)
    if action is not None:
        await act(update, context, 2, action)

async def act_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = get_action(update, 2)
    if action is not None:
        await act(update, context, 2, action)

async def act_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = get_action(update, 2)
    if action is not None:
        await act(update, context, 2, action)

async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global world_dict

    world = get_world(update)
    if world.selected_npc_index == 0:
        await send_message(update, context, "You are not talking to anyone.")
        return
    
    parts = update.message.text.split(' ', 1)
    if len(parts) == 1:
        return None
    else:
        action = 'say "{}"'.format(parts[1])
        await act(update, context, world.selected_npc_index, action)

async def addnpc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global world_dict

    world = get_world(update)
    
    parts = update.message.text.split(' ', 1)
    if len(parts) == 1:
        return None
        
    npc_parts = parts[1].split('|')
    description = npc_parts[0].strip()
    appearance = npc_parts[1].strip()

    npc = NPC(description=description, appearance=appearance)
    world.add_npc(npc)

    await send_message(update, context, "NPC added")

def main():
    db.connect_to_db(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("newgame", new_game))
    application.add_handler(CommandHandler("n", go_north))
    application.add_handler(CommandHandler("s", go_south))
    application.add_handler(CommandHandler("e", go_east))
    application.add_handler(CommandHandler("w", go_west))
    application.add_handler(CommandHandler("look", look))
    application.add_handler(CommandHandler("who", who))
    application.add_handler(CommandHandler("map", show_map))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("1", act_1))
    application.add_handler(CommandHandler("2", act_2))
    application.add_handler(CommandHandler("3", act_3))
    application.add_handler(CommandHandler("4", act_4))
    application.add_handler(CommandHandler("talk", talk))
    application.add_handler(CommandHandler("addnpc", addnpc))

    application.run_polling(stop_signals=None)

    db.close_db_connection()

if __name__ == '__main__':
    main()