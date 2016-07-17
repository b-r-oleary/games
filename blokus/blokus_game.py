from __future__ import division

# import kivy functions for the app functions
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window

# additional imports
import copy
import numpy as np  # for array manupulation and math

# other classes within the blokus module
from game_widgets import GameBoard, BlokusPiece, TransformBubble, HelperDot, FlybyLabel
from game import Game
from player import Player
from initial_positions import InitialPositions
from settings import Settings
from piece import Piece
from game_methods import find_corners, find_available_moves


class BlokusApp(App):
    """
    this object is a Kivy app that houses the application itself
    and the clock scheduler system.
    """

    icon  = './blokus/images/icon.png'
    title = 'Blokus'

    def __init__(self, *args, **kwargs):
        """
        Initialize the app by creating a settings object
        that houses some of the specific constants required
        for instantiating the app. The default settings
        can be overwritten by keyword argument inputs here
        """
        self.settings = Settings(**kwargs)
        super(BlokusApp, self).__init__(*args, **kwargs)
        return

    def build(self):
        """
        create a blokus game widget within the app, and schedule
        the updates for this widget
        """
        game = BlokusGame(self.settings)
        Clock.schedule_interval(game.update, self.settings.frame_rate)
        return game


class BlokusGame(Widget):
    """
    this is the primary widget that controls the game flow.

    methods:
    rotate_initial_configuration: given an array of starting
        positions for the pieces for playerID=0, rotate the 
        starting positions to make them applicable for playerID != 0

    update: on each time step, we need to update the positions of the
        pieces on the board. For example, piece has to move with the
        cursor when I grab it, and must snap to grid when I release it.
        When I am holding a piece, the menu bar has to move with the
        piece. If the timers for the helper dots expire, they must disappear, etc...
    
    flip_active_piece: performs a flip operation from menu bar on a piece
    rotate_ccw_active_piece: performs a counter clockwise rotation
        operation from the menu bar on the active piece
    rotate_cw_active_piece: performs a clockwise rotation
        operation from the menu bar on the active piece
    close_instructions: removes the menu bar when requested by the
        menu, or after a time expiration
    add_helpers: find valid connection corners for the current playerID
        and add stars to the board indicating where they can place pieces
    remove_helpers: remove the helpers from the board
    add_piece: after committing to making a move, fix it to the board
        permanantly. does not allow invalid moves.
    on_touch_up: after releasing a piece, if it is on the board,
        but it is not your turn, it will return to its previous position
        off the board. If it is off the board, it will accept the new
        location off the board.
    """

    # initialize the game properties:
    board = ObjectProperty(None)
    piece = ObjectProperty(None)
    active_piece = NumericProperty(-1)
    active_piece_timer = NumericProperty
    instructions = ObjectProperty(None)

    def __init__(self, settings, **kwargs):
        """
        this widget takes a settings object
        as an argument, which is passed from the
        BlokusApp.
        """

        super(BlokusGame, self).__init__(**kwargs)

        self.settings = settings

        with self.canvas:
            # create a game board
            self.game = Game(dimension=self.settings.board_size, 
                             num_players=self.settings.num_players)

            # initialize a list of helper widgets (stars that indicate
            # where you can place a piece that appear if you attempt to
            # place a piece in an invalid location) and a timer
            # for how long the helper widgets have been present.
            self.helpers = []
            self.helper_timer = 0

            # this is an initialization of a timer of how long a piece has
            # been active.
            self.active_piece_timer = 0

            # initialize a label (an image including text that flies
            # across the screen), and a label timer.
            self.label = -1
            self.label_timer = 0

            # specify the size of the board in units of pixels
            self.board.size = tuple([self.settings.board_size_d] * 2)

            # indicate whether or not the game is active.
            self.game_active = True

            # specify the position of the board within the screen
            # in units of pixels.
            self.board.x = self.settings.corner_offset_d[0]
            self.board.y = self.settings.corner_offset_d[1]

            # create all of the players in the game with the specified
            # types and the specified strategies if they are AI players.
            self.players = []
            for i in xrange(self.settings.num_players):
                self.players += [Player(i,
                                  player_type=self.settings.player_types[i],
                                  strategy=self.settings.player_strategies[i],
                                  weights=self.settings.player_weights[i])]

            # initialize the current attempted move.
            self.current_move = [-1, []]

            # these are the initial positions for all of the pieces.
            # these locations are outside of the board and are fairly optimally
            # packed.
            (initial_positions, 
             initial_rotations, 
             initial_parities ,) = \
                        InitialPositions(self.settings.screen_mode).get()

            # choose random initial configurations for the pieces:
            start_inds = list(np.random.randint(0,
                                    len(initial_positions),
                                    size=[self.settings.num_players])
                         )

            positions = [0] * self.settings.num_players
            rotations = [0] * self.settings.num_players
            parities  = [0] * self.settings.num_players

            for playerID in range(self.settings.num_players):
                if self.settings.screen_mode == 'all_players':
                    offset = (0, 0)
                    rotate_initial_configuration = playerID
                elif self.settings.screen_mode == 'single_player':
                    offset = (self.settings.board_size, 0)
                    rotate_initial_configuration = 1
                # rotate the initial positions since the initial positions
                # are only specified for playerID = 0.
                positions[playerID], rotations[playerID], parities[playerID] = \
                self.rotate_initial_configuration(
                    initial_positions[start_inds[playerID]], 
                    initial_rotations[start_inds[playerID]], 
                    initial_parities[start_inds[playerID]], 
                    rotate_initial_configuration, 
                    dimension=self.settings.current_grid_size, 
                    offset=offset)

            # initialize the pieces for each player in the game.
            self.pieces = []
            for i in range(self.settings.num_pieces * 
                           self.settings.num_players):

                pieceID = i % self.settings.num_pieces + 1
                playerID = i // self.settings.num_pieces

                rotation = rotations[playerID][pieceID]
                parity = parities[playerID][pieceID]

                piece = BlokusPiece(
                    d=self.settings.d,
                    pieceID=pieceID,
                    playerID=playerID,
                    rotation=rotation,
                    parity=parity)

                if self.settings.screen_mode == 'all_players':
                    position = (
                        self.x + piece.d * positions[playerID][pieceID][0],
                        self.y + piece.d * positions[playerID][pieceID][1])
                elif self.settings.screen_mode == 'single_player':
                    position = (self.x + piece.d * (positions[playerID][pieceID][0] + self.settings.piece_offset[0]),
                                self.y + piece.d * (positions[playerID][pieceID][1] + self.settings.piece_offset[1] - .5))

                piece.home = position

                wait_position = (self.settings.current_screen_size[0] + 
                                 np.random.randint(self.settings.current_screen_size[0] + 2 * self.settings.d, 
                                                   1.5 * self.settings.current_screen_size[0] + 2 * self.settings.d), 
                                 np.random.randint(-self.settings.current_screen_size[1] / 2, 3 * self.settings.current_screen_size[1] / 2)
                                 )

                piece.wait = wait_position
                if ((playerID == 0) or 
                    (self.settings.show_all and self.settings.screen_mode == 'all_players')):
                    piece.pos = position
                    piece.setpoint = position
                else:
                    piece.pos = wait_position
                    piece.setpoint = wait_position
                self.pieces = self.pieces + [piece]
                self.add_widget(piece)

        # initialize the menu bar that enables manipulation of the pieces
        # and move commits.
        self.instructions = TransformBubble()
        self.instructions.rotate_cw.bind(
            on_release=self.rotate_cw_active_piece)
        self.instructions.flip.bind(on_release=self.flip_active_piece)
        self.instructions.rotate_ccw.bind(
            on_release=self.rotate_ccw_active_piece)
        self.instructions.close.bind(on_release=self.close_instructions)
        self.instructions.commit.bind(on_release=self.add_piece)

        # add helpers for the start of the game to show the start points.
        self.add_helpers()

    def rotate_initial_configuration(self,positions,
                                          rotations,
                                          parities,
                                          playerID,
                                     dimension=(42,42),
                                     offset=(0,0)):
        """
        rotate an initial configuration (which was configured for player 1), so that
        I can use it for a different player
        """
        pieces = [
            Piece(
                pieceID,
                playerID,
                rotation=rotations[pieceID],
                parity=parities[pieceID]
                ) 
            for pieceID in range(1, self.settings.num_pieces + 1)]

        new_positions = {}
        new_rotations = {}
        new_parities = {}

        playerID = playerID % self.settings.num_players

        for i in range(1, len(pieces) + 1):
            pos = positions[i]
            pos = (pos[0] + offset[0], pos[1] + offset[1])
            size = pieces[i - 1].geometry.shape
            if playerID == 0:
                new_position = pos
            elif playerID == 1:
                new_position = (pos[1], dimension[1] - pos[0] - size[0])
            elif playerID == 2:
                new_position = (
                    dimension[0] - pos[0] - size[0],
                    dimension[1] - pos[1] - size[1])
            elif playerID == 3:
                new_position = (dimension[0] - pos[1] - size[1], pos[0])

            new_rotation = rotations[i] - playerID
            new_parity = parities[i]

            new_positions[i] = new_position
            new_rotations[i] = new_rotation
            new_parities[i] = new_parity

        return new_positions, new_rotations, new_parities

    def update(self, dt):
        """
        update the gameboard given that the time between the last update
        and now has been dt.
        """

        # move the menu above the active piece so that it stays in sync with
        # the active piece
        if self.active_piece >= 0:
            self.instructions.y = self.pieces[
                self.active_piece].y + self.pieces[self.active_piece].height + 6
            self.instructions.center_x = self.pieces[
                self.active_piece].center_x
            if self.instructions.y + self.instructions.height > self.settings.current_screen_size[1]:
                self.instructions.y = self.settings.current_screen_size[1] - self.instructions.height
            if self.instructions.y < 0:
                self.instructions.y = 0
            if self.instructions.x < 0:
                self.instructions.x = 0
            if self.instructions.x + self.instructions.width > self.settings.current_screen_size[0]:
                self.instructions.x = self.settings.current_screen_size[0] - self.instructions.width

        moving = False
        for i in range(len(self.pieces)):
            # update the position of all of the pieces
            self.pieces[i].update()
            moving = (moving or self.pieces[i].go_to_setpoint)

            if self.pieces[i].playerID == self.game.current_playerID:

                # if one of the pieces has just been grabbed,
                # mark that piece as the active piece,
                # move that piece to the front and add the instructions
                # menu above that piece.
                if self.pieces[i].grabbed:
                    active_piece = i
                    if not(self.active_piece == active_piece):
                        self.active_piece = i
                        self.remove_widget(self.pieces[i])
                        self.add_widget(self.pieces[i])

                        self.remove_widget(self.instructions)
                        self.add_widget(self.instructions)
                        self.active_piece_timer = 0

        # if there is currently an active piece increment the active piece
        # counter
        if self.active_piece >= 0:
            self.active_piece_timer += 1

        # if the active piece counter exceeds a threshold of 5 seconds without
        # any use, then remove the menu from above that piece and unmark it as
        # active.
        if self.active_piece_timer > 60 * 15:
            self.close_instructions()

        if len(self.helpers) > 0:
            self.helper_timer += 1

        if self.helper_timer > 60 * 15:
            for helper in self.helpers:
                self.remove_widget(helper)
            self.helpers = []

        if not(self.label < 0):
            self.label.update()
            self.label_timer += 1
            if not self.label.go_to_setpoint:
                self.label.setpoint = (
                    np.random.randint(
                        self.settings.current_screen_size[0] +
                        self.label.width,
                        1.5 *
                        self.settings.current_screen_size[0] +
                        self.label.width),
                    np.random.randint(
                        0,
                        self.settings.current_screen_size[1]))
                self.label.go_to_setpoint = True
            if self.label_timer >= 60 * 3:
                self.remove_widget(self.label)
                self.label = -1

        if self.game_active:
            if not moving:
                player = self.players[self.game.current_playerID]
                if player.player_type != 'human':
                    if self.current_move[0] == -1:
                        move = player.make_move(self.game, self.pieces)
                        position = move['position']
                        ind = move['index']
                        print move
                        if self.pieces[
                                ind].playerID != self.game.current_playerID:
                            print 'there is something wrong with the playerIDs'
                            print self.pieces[ind].playerID
                            print self.game.current_playerID

                        self.current_move = [ind, move]
                        if ind >= 0:
                            self.pieces[ind].piece.reset_orientation(
                                rotation=move['rotation'], parity=move['parity'])
                            self.pieces[ind].setpoint = (
                                (position[0] + self.settings.corner_offset[0]) * self.settings.d,
                                (position[1] + self.settings.corner_offset[1]) * self.settings.d)
                            self.pieces[ind].go_to_setpoint = True
                            self.active_piece = ind
                            self.remove_widget(self.pieces[ind])
                            self.add_widget(self.pieces[ind])
                    else:
                        self.active_piece = self.current_move[0]
                        self.add_piece()
                        self.current_move = [-1, []]

    def flip_active_piece(self, *l):
        # flip the active piece vertically
        self.pieces[self.active_piece].flip()
        self.pieces[self.active_piece].update_blocks()
        self.active_piece_timer = 0

    def rotate_ccw_active_piece(self, *l):
        # rotate the active block counterclockwise by 90 degrees
        self.pieces[self.active_piece].rotate(rotation=1)
        self.pieces[self.active_piece].update_blocks()
        self.active_piece_timer = 0

    def rotate_cw_active_piece(self, *l):
        # rotate the active block clockwise by 90 degrees
        self.pieces[self.active_piece].rotate(rotation=-1)
        self.pieces[self.active_piece].update_blocks()
        self.active_piece_timer = 0

    def close_instructions(self, *l):
        # close the little menu above the active block.
        self.active_piece = -1
        self.remove_widget(self.instructions)

    def add_helpers(self):
        corners = self.game.find_available_corners()
        for corner in corners:
            Size = 3 * self.settings.d / 2.
            helper = HelperDot(
                size=(Size, Size),
                pos=(
                    (corner[0] + self.settings.corner_offset[0] + .5) * self.settings.d - Size / 2,
                    (corner[1] + self.settings.corner_offset[1] + .5) * self.settings.d - Size / 2))
            self.helpers += [helper]
            self.add_widget(helper)
        self.helper_timer = 0

        if self.active_piece >= 0:
            self.remove_widget(self.pieces[self.active_piece])
            self.add_widget(self.pieces[self.active_piece])

    def remove_helpers(self):
        for helper in self.helpers:
            self.remove_widget(helper)
        self.helpers = []

    def add_piece(self, *l):

        if self.players[self.game.current_playerID].player_type == 'human':
            position = self.pieces[self.active_piece].pos
        else:
            position = self.pieces[self.active_piece].setpoint

        position = (int(np.round(position[0] / self.settings.d - self.settings.corner_offset[0])), 
                    int(np.round(position[1] / self.settings.d - self.settings.corner_offset[1])))
        # now position is the integer coordinates on the board
        self.remove_helpers()
        # attempt to place the piece on the gameboard:
        problem = self.game.place_piece(
            self.pieces[self.active_piece].piece, position)

        if problem == '':
            self.remove_widget(self.instructions)
            self.remove_widget(self.pieces[self.active_piece])
            self.board.place_piece(self.pieces[self.active_piece], position, 
                                   self.settings.d, self.settings.corner_offset)
            self.pieces.pop(self.active_piece)
            self.active_piece = -1
            self.on_touch_up((0, 0))

            if self.game.round == 0:
                self.add_helpers()

            for i in range(len(self.pieces)):
                if ((self.pieces[i].playerID == self.game.current_playerID) or
                    (self.settings.show_all and self.settings.screen_mode == 'all_players')):
                    self.pieces[i].setpoint = self.pieces[i].home
                else:
                    self.pieces[i].setpoint = self.pieces[i].wait
                self.pieces[i].go_to_setpoint = True

            counter = 0
            while counter < 4:
                # check to see if any moves are possible
                moves = find_available_moves(self.game, self.pieces, num=1)
                if len(moves) == 0:
                    print 'skipping a turn'
                    self.game.increment_turn()
                    counter += 1
                    for i in range(len(self.pieces)):
                        if ((self.pieces[i].playerID == self.game.current_playerID)  or
                            (self.settings.show_all and self.settings.screen_mode == 'all_players')):
                            self.pieces[i].setpoint = self.pieces[i].home
                        else:
                            self.pieces[i].setpoint = self.pieces[i].wait
                        self.pieces[i].go_to_setpoint = True
                else:
                    break

            if counter >= 4:
                print 'game over'
                self.game_active = False
                if not(self.label < 0):
                    self.remove_widget(self.label)
                self.label = FlybyLabel(instance='game_over', d=self.settings.d)
                self.label.pos = (np.random.randint(-self.settings.current_screen_size[0] - self.label.width, -self.label.width),
                                  np.random.randint(0, self.settings.current_screen_size[1]))
                self.label.setpoint = (self.center[0] - self.label.width / 2.,
                                       self.center[1] - self.label.height / 2.)
                self.label.go_to_setpoint = True
                self.label_timer = 0
                self.add_widget(self.label)

        else:
            print problem

            self.add_helpers()
            if not(self.label < 0):
                self.remove_widget(self.label)
            self.label = FlybyLabel(instance='really', d=self.settings.d)
            self.label.pos = (np.random.randint(-self.settings.current_screen_size[0] - self.label.width, -self.label.width),
                              np.random.randint(0, self.settings.current_screen_size[1]))
            self.label.setpoint = (self.center[0] - self.label.width / 2.,
                                   self.center[1] - self.label.height / 2.)
            self.label.go_to_setpoint = True
            self.label_timer = 0
            self.add_widget(self.label)

    def on_touch_up(self, touch):
        for i in xrange(len(self.pieces)):
            if self.board.collide_widget(self.pieces[i]):
                if self.pieces[i].playerID != self.game.current_playerID:
                    self.pieces[i].go_to_setpoint = True
            else:
                if ((self.pieces[i].playerID == self.game.current_playerID) and 
                    (self.pieces[i].setpoint == self.pieces[i].home)):
                    pos = self.pieces[i].pos
                    self.pieces[i].home = (
                        np.round(
                            pos[0] /
                            self.settings.d -
                            self.settings.corner_offset[0]) *
                        self.settings.d +
                        self.settings.corner_offset[0] *
                        self.settings.d,
                        np.round(
                            pos[1] /
                            self.settings.d -
                            self.settings.corner_offset[1]) *
                        self.settings.d +
                        self.settings.corner_offset[1] *
                        self.settings.d)