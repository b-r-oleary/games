from __future__ import division
import sys
from blokus import BlokusApp

if __name__ == '__main__':

    screen_mode  = 'all_players'
    player_types = ['ai'] * 4
    show_all     = True

    arguments = sys.argv
    while len(arguments) > 1:
        argument = arguments.pop(0)
        if argument == 'display':
            value = arguments.pop(0)
            screen_mode = value
        if argument == 'players':
            value = int(arguments.pop(0))
            player_types = ['human'] * value + ['ai'] * (4 - value)
        if argument == 'show_all':
            value = ((arguments.pop(0)).lower() == 'true')
            show_all = value

    BlokusApp(screen_mode=screen_mode,
              player_types=player_types,
              show_all=show_all,
              ).run()