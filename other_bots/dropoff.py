#!/usr/bin/env python3

# Import the Halite SDK, which will let you interact with the game.
import hlt
from hlt import *

import random
import logging


def move_to_drop(ship):
    move = Direction.North
    if len(game.me.get_dropoffs()) > 0:
        if game_map.calculate_distance(ship.position, game.me.shipyard.position) < game_map.calculate_distance(
                ship.position, list(game.me.get_dropoffs())[0].position):
            move = game_map.get_unsafe_moves(ship.position, game.me.shipyard.position)[0]
        elif ship.position != list(game.me.get_dropoffs())[0].position:
            move = game_map.get_unsafe_moves(ship.position, list(game.me.get_dropoffs())[0].position)[0]
    elif ship.position != game.me.shipyard.position:
        move = game_map.get_unsafe_moves(ship.position, game.me.shipyard.position)[0]
    return move


def check_area(position):
    val = game_map[position].halite_amount + game_map[position.directional_offset(Direction.North)].halite_amount + \
          game_map[position.directional_offset(Direction.South)].halite_amount + game_map[
              position.directional_offset(Direction.East)].halite_amount + game_map[
              position.directional_offset(Direction.West)].halite_amount + game_map[
              position.directional_offset(Direction.North).directional_offset(Direction.West)].halite_amount + game_map[
              position.directional_offset(Direction.North).directional_offset(Direction.East)].halite_amount + game_map[
              position.directional_offset(Direction.South).directional_offset(Direction.West)].halite_amount + game_map[
              position.directional_offset(Direction.South).directional_offset(Direction.East)].halite_amount
    return val


def get_hotspot(map):
    hotspot = game.me.shipyard.position
    hspt_val = check_area(hotspot)
    for search_size in range(1, (map.width // 2)):
        # logging.info("SEARCH SIZE = {}.".format(search_size))
        for a in range(-search_size, search_size + 1, 2 * search_size):
            # logging.info("a:" + str(a))
            for b in range(-search_size, search_size + 1, 1):
                # logging.info("b:" + str(b))
                pos_1 = Position(game.me.shipyard.position.x + a, game.me.shipyard.position.y + b)
                pos_2 = Position(game.me.shipyard.position.x + b, game.me.shipyard.position.y + a)
                pos_val_1 = check_area(pos_1)
                pos_val_2 = check_area(pos_2)
                # logging.info("Checking pos1 : " + format(pos_1) + "  --  pos_val is: " + str(pos_val_1))
                # logging.info("Checking pos2 : " + format(pos_2) + "  --  pos_val is: " + str(pos_val_2))
                if pos_val_1 > hspt_val:
                    hspt_val = pos_val_1
                    hotspot = pos_1
                if pos_val_2 > hspt_val:
                    hspt_val = pos_val_2
                    hotspot = pos_2
                if hspt_val > (1600):
                    break
            else:
                continue
            break
        else:
            continue
        break
    return game_map.normalize(hotspot)


# This game object contains the initial game state.
game = hlt.Game()

# Respond with your name.
game.ready("speegeeBot")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))
return_amount = 850
turn = 0
game_map = game.game_map
me = game.me
hotspot = get_hotspot(game_map)
hstp_search_cnt = 0
dart_trig = 0
dart_id = -1
logging.info("Found initial hotspot, value is " + str(check_area(hotspot)))

while True:
    # Get the latest game state.
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    # calculate relevant values
    turn += 1
    num_ships = len(me.get_ships())
    if check_area(hotspot) < 2500 and hstp_search_cnt < 25:
        hstp_search_cnt += 1
        logging.info("###### Finding hotspot ( " + str(hstp_search_cnt) + " )")
        hotspot = get_hotspot(game_map)
        logging.info("###### Hotspot found " + format(hotspot) + " -- value is " + str(check_area(hotspot)))

    # A command queue holds all the commands you will run this turn.
    command_queue = []

    # logging.info("Movement Phase: turn " + str(turn) + " : " + str(turn_limit) + ", the hotspot is " + format(hotspot))

    # command ships
    for ship in me.get_ships():
        move_dir = random.choice([Direction.North, Direction.South, Direction.East, Direction.West])
        stay = 0
        dropoff = 0
        if len(game.me.get_dropoffs()) < 1 and game_map.calculate_distance(ship.position,game.me.shipyard.position) > 10 and game_map.calculate_distance(hotspot, game.me.shipyard.position) > 10 and game.me.halite_amount > 5000:
            if dart_trig == 0:
                dart_id = ship.id
                dart_trig = 1
                logging.info("######---- " + str(dart_id) + " is dart ---####### ")
            elif ship.id == dart_id and ship.position != hotspot:
                move_dir = game_map.get_unsafe_moves(ship.position, hotspot)[0]
            elif ship.id == dart_id and ship.position == hotspot:
                dropoff = 1

        elif ship.halite_amount > 700 + turn * .4:
            move_dir = move_to_drop(ship)
        elif game_map[ship.position].halite_amount > 60:
            stay = 1
        elif check_area(ship.position) < 850 and ship.position != hotspot:
            move_dir = game_map.get_unsafe_moves(ship.position, hotspot)[0]
        else:
            best = 0
            for d in Direction.get_all_cardinals():
                if best < game_map[ship.position.directional_offset(d)].halite_amount:
                    best = game_map[ship.position.directional_offset(d)].halite_amount
                    move_dir = d

        rand = random.choice([Direction.North, Direction.South, Direction.East, Direction.West])
        if constants.MAX_TURNS - turn < game_map.calculate_distance(ship.position, game.me.shipyard.position) + 6 and game.me.shipyard.position != ship.position:
            move_dir = move_to_drop(ship)
            command_queue.append(ship.move(move_dir))
            game_map[ship.position.directional_offset(move_dir)].mark_unsafe(ship)
            logging.info("ship @ " + format(ship.position) + " running home for end " + format(
                ship.position.directional_offset(move_dir)))
        elif dropoff == 1:
            logging.info("######---- Making dropoff ---####### ")
            logging.info("ship @ " + format(ship.position) + " making dropoff")
            command_queue.append(ship.make_dropoff())
        elif stay == 0 and not game_map[ship.position.directional_offset(move_dir)].is_occupied:
            command_queue.append(ship.move(move_dir))
            game_map[ship.position.directional_offset(move_dir)].mark_unsafe(ship)
            # logging.info("ship @ " + format(ship.position) + " moving to " + format(ship.position.directional_offset(move_dir)))
        elif stay == 0 and not game_map[ship.position.directional_offset(rand)].is_occupied:
            command_queue.append(ship.move(rand))
            game_map[ship.position.directional_offset(rand)].mark_unsafe(ship)
            # logging.info("ship @ " + format(ship.position) + " making random move to " + format(ship.position.directional_offset(rand)))
        else:
            command_queue.append(ship.stay_still())
            game_map[ship.position].mark_unsafe(ship)
            # logging.info("ship @ " + format(ship.position) + "stayed still and collected {}.".format(game_map[ship.position].halite_amount / 4))

    # spawn ships from shipyard
    if not game_map[
        game.me.shipyard.position].is_occupied and me.halite_amount > 999 and turn / constants.MAX_TURNS < .4:
        command_queue.append(game.me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)