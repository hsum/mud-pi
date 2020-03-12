#!/usr/bin/env python

"""A complex Multi-User Dungeon (MUD) game. Players can talk to each
other, examine their surroundings and move between rooms.

Some ideas for things to try adding:
    * More rooms to explore
    * An 'emote' command e.g. 'emote laughs out loud' -> 'Mark laughs
        out loud'
    * A 'whisper' command for talking to individual players
    * A 'shout' command for yelling to players in all rooms
    * Items to look at in rooms e.g. 'look fireplace' -> 'You see a
        roaring, glowing fire'
    * Items to pick up e.g. 'take rock' -> 'You pick up the rock'
    * Monsters to fight
    * Loot to collect
    * Saving players accounts between sessions
    * A password login
    * A shop from which to buy items

author: Mark Frimston - mfrimston@gmail.com
"""

import sys
import time

# import the MUD server class
from mudserver import MudServer


# structure defining the rooms in the game. Try adding more rooms to the game!
rooms = {
    "Tavern": {
        "description": "You're in a cozy tavern warmed by an open fire.",
        "exits": {"outside": "Outside"},
    },
    "Outside": {
        "description": "You're standing outside a tavern. It's raining.",
        "exits": {"inside": "Tavern"},
    }
}

# stores the players in the game
players = {}


def command_help(mud, player_id, command, params):
    # send the player back the list of possible commands
    mud.send_message(player_id, "Commands:")
    mud.send_message(player_id, "  say <message>  - Says something out loud, "
                         + "e.g. 'say Hello'")
    mud.send_message(player_id, "  look           - Examines the "
                         + "surroundings, e.g. 'look'")
    mud.send_message(player_id, "  go <exit>      - Moves through the exit "
                         + "specified, e.g. 'go outside'")

def command_say(mud, player_id, command, params):
    # 'say' command
    # go through every player in the game
    for pid, pl in players.items():
        # if they're in the same room as the player
        if players[pid]["room"] == players[player_id]["room"]:
            # send them a message telling them what the player said
            mud.send_message(pid, "{} says: {}".format(
                                        players[player_id]["name"], ' '.join(params)))

def command_look(mud, player_id, command, params):
    # 'look' command
    # store the player's current room
    rm = rooms[players[player_id]["room"]]

    # send the player back the description of their current room
    mud.send_message(player_id, rm["description"])

    playershere = []
    # go through every player in the game
    for pid, pl in players.items():
        # if they're in the same room as the player
        if players[pid]["room"] == players[player_id]["room"]:
            # ... and they have a name to be shown
            if players[pid]["name"] is not None:
                # add their name to the list
                playershere.append(players[pid]["name"])

    # send player a message containing the list of players in the room
    mud.send_message(player_id, "Players here: {}".format(
                                            ", ".join(playershere)))

    # send player a message containing the list of exits from this room
    mud.send_message(player_id, "Exits are: {}".format(
                                            ", ".join(rm["exits"])))

def command_go(mud, player_id, command, params):
    # 'go' command
    # store the exit name
    ex = ' '.join(params).lower()

    # store the player's current room
    rm = rooms[players[player_id]["room"]]

    # if the specified exit is found in the room's exits list
    if ex in rm["exits"]:

        # go through all the players in the game
        for pid, pl in players.items():
            # if player is in the same room and isn't the player
            # sending the command
            if players[pid]["room"] == players[player_id]["room"] \
                    and pid != player_id:
                # send them a message telling them that the player
                # left the room
                mud.send_message(pid, "{} left via exit '{}'".format(
                                              players[player_id]["name"], ex))

        # update the player's current room to the one the exit leads to
        players[player_id]["room"] = rm["exits"][ex]
        rm = rooms[players[player_id]["room"]]

        # go through all the players in the game
        for pid, pl in players.items():
            # if player is in the same (new) room and isn't the player
            # sending the command
            if players[pid]["room"] == players[player_id]["room"] \
                    and pid != id:
                # send them a message telling them that the player
                # entered the room
                mud.send_message(pid,
                                 "{} arrived via exit '{}'".format(
                                              players[player_id]["name"], ex))

        # send the player a message telling them where they are now
        mud.send_message(player_id, "You arrive at '{}'".format(
                                                  players[player_id]["room"]))

    # the specified exit wasn't found in the current room
    else:
        # send back an 'unknown exit' message
        mud.send_message(player_id, "Unknown exit '{}'".format(ex))
#print(list(
#    (k.replace('command_', ''), v) for k, v in locals().items() if callable(v) and k.startswith('command_')
#))
commands = {
    k.replace('command_', ''): v for k, v in locals().items() if callable(v) and k.startswith('command_')
}

# start the server
mud = MudServer()

# main game loop. We loop forever (i.e. until the program is terminated)
while True:

    # pause for 1/5 of a second on each loop, so that we don't constantly
    # use 100% CPU time
    time.sleep(0.2)

    # 'update' must be called in the loop to keep the game running and give
    # us up-to-date information
    mud.update()

    # go through any newly connected players
    for player_id in mud.events_new_player:

        # add the new player to the dictionary, noting that they've not been
        # named yet.
        # The dictionary key is the player's id number. We set their room to
        # None initially until they have entered a name
        # Try adding more player stats - level, gold, inventory, etc
        players[player_id] = {
            "name": None,
            "room": None,
        }

        # send the new player a prompt for their name
        mud.send_message(player_id, "What is your name?")

    # go through any recently disconnected players
    for player_id in mud.events_player_left:

        # if for any reason the player isn't in the player map, skip them and
        # move on to the next one
        if player_id not in players:
            continue

        # go through all the players in the game
        for pid, pl in players.items():
            # send each player a message to tell them about the disconnected
            # player
            mud.send_message(pid, "{} quit the game".format(
                                                        players[player_id]["name"]))

        # remove the player's entry in the player dictionary
        del(players[player_id])

    # go through any new commands sent from players
    for player_id, (command, params) in mud.events_command:

        # if for any reason the player isn't in the player map, skip them and
        # move on to the next one
        if player_id not in players:
            continue

        # if the player hasn't given their name yet, use this first command as
        # their name and move them to the starting room.
        if players[player_id]["name"] is None:

            players[player_id]["name"] = command
            players[player_id]["room"] = "Tavern"

            # go through all the players in the game
            for pid, pl in players.items():
                # send each player a message to tell them about the new player
                mud.send_message(pid, "{} entered the game".format(
                                                        players[player_id]["name"]))

            # send the new player a welcome message
            mud.send_message(player_id, "Welcome to the game, {}. ".format(
                                                           players[player_id]["name"])
                             + "Type 'help' for a list of commands. Have fun!")

            # send the new player the description of their current room
            mud.send_message(player_id, rooms[players[player_id]["room"]]["description"])

        # each of the possible commands is handled below. Try adding new
        # commands to the game!
        else:
            func = commands.get(command)
            if func:
                func(mud, player_id, command, params)
            else:
                # some other, unrecognised command
                # send back an 'unknown command' message
                mud.send_message(player_id, "Unknown command '{}'".format(command))
