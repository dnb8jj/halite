#!/usr/bin/env python3

# Import the Halite SDK, which will let you interact with the game.
import hlt
from hlt import *

import random
import logging


def check_area(position):
    val = game_map[position].halite_amount
    for d in Direction.get_all_cardinals():
        val += game_map[position.directional_offset(d)].halite_amount + game_map[
            position.directional_offset(d).directional_offset(Direction.North)].halite_amount + game_map[
                   position.directional_offset(d).directional_offset(Direction.South)].halite_amount
    return val;


def get_hotspot(game_map):
    hotspot = Position(1, 1)
    for h in range(game_map.height):
        for w in range(game_map.width):
            sp = Position(h, w)
            if check_area(sp) > check_area(hotspot):
                hotspot = sp
    return hotspot;


# This game object contains the initial game state.
game = hlt.Game()

# Respond with your name.
game.ready("speegeeBot")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))
turn = 1
while True:
    # Get the latest game state.
    game.update_frame()
    turn += 1

    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map
    hotspot = get_hotspot(game_map)
    logging.info("it is turn " + str(turn) + " the hotspot is " + format(hotspot))
    # A command queue holds all the commands you will run this turn.
    command_queue = []

    # command ships
    for ship in me.get_ships():
        if ship.position == game.me.shipyard.position:
            command_queue.append(ship.move(game_map.naive_navigate(ship, hotspot)))
        elif ship.halite_amount > 800 or (game_map.calculate_distance(ship.position,
                                                                      game.me.shipyard.position) < 5 and ship.halite_amount > 300) and not \
        game_map[game.me.shipyard.position].is_occupied:
            #        elif ship.halite_amount / (game_map.calculate_distance(ship.position, game.me.shipyard.position) + .1) > 25 and not game_map[game.me.shipyard.position].is_occupied:
            command_queue.append(ship.move(game_map.naive_navigate(ship, game.me.shipyard.position)))
        elif game_map[ship.position].halite_amount > 150:
            command_queue.append(ship.stay_still())
            game_map[ship.position].mark_unsafe(ship)
            logging.info("stayed still and collected {}.".format(game_map[ship.position].halite_amount / 4))
        else:
            move_dir = random.choice([Direction.North, Direction.South, Direction.East, Direction.West])
            best = game_map[ship.position].halite_amount
            hspt = []
            hspt = game_map.get_unsafe_moves(ship.position, hotspot)
            if game_map.calculate_distance(ship.position, game.me.shipyard.position) > 6 and check_area(
                    ship.position) < 3600 and not game_map[ship.position.directional_offset(hspt[0])].is_occupied:
                move_dir = hspt[0]
            else:
                for d in Direction.get_all_cardinals():
                    if best < game_map[ship.position.directional_offset(d)].halite_amount and not game_map[
                        ship.position.directional_offset(d)].is_occupied:
                        best = game_map[ship.position.directional_offset(d)].halite_amount
                        move_dir = d
            command_queue.append(ship.move(move_dir))
            game_map[ship.position.directional_offset(move_dir)].mark_unsafe(ship)
            logging.info(
                "ship @ " + format(ship.position) + " move to " + format(ship.position.directional_offset(move_dir)))

    # spawn ships from shipyard
    if not game_map[game.me.shipyard.position].is_occupied and me.halite_amount > 999:  # and len(me.get_ships()) > 12:
        command_queue.append(game.me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
