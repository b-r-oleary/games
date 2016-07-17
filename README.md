# Blokus

This a blokus game built using the [kivy](https://kivy.org/docs/installation/installation.html) platform in python with an additional dependence on numpy for 2d array manipulation.

The application can be started from the command line with the command line driver script `blokus.py`.

There are few options to modify the behavior of the game:

- `players`: Number of human players in the game (0 - 4), the default is a demo mode with 0 human players.
- `display`: Type of display for the game. The options are `all_players`, which shows all of the players sets of pieces at once with a screen size that is suitable for desktop, or `single_player`, which shows only a single players pieces at a time with a screen size that is suitable for mobile. This is `all_players` by default.
- `show_all`: If the display is set to `all_players`, then you have the option of showing the pieces for all players, or only the pieces for the player whose turn it is currently. This should be a boolean `True` or `False`, and is set to `True` by default.

This game currently uses some simple heuristics for the AI that has been implimented, but in the future, I would like to create a program that can optimize the performance of the AI using re-enforcement learning. Additionally, I would like to impliment an SQLite database for locally storing each of the games that is played with the outcome, timestamps, and AI model parameters.