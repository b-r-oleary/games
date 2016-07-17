# import kivy functions for the app functions
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.bubble import Bubble
from kivy.graphics import Rectangle, Ellipse, Color
from kivy.uix.image import Image
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window

# additional imports
import copy
import numpy as np  # for array manupulation and math
import sys
sys.path.insert(0, './code')

from code import Gameboard

class BlokusGame(Widget):
    # initialize the game properties:
    board = ObjectProperty(None)
    piece = ObjectProperty(None)
    active_piece = NumericProperty(-1)
    active_piece_timer = NumericProperty
    instructions = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(BlokusGame, self).__init__(**kwargs)

        # player_types=['human']+['ai']*3
        #player_strategies=['human']+['markov rule']+['dual rule']*2
        # player_weights=[[5,10,2,1,40,20],[5,10,10,1,40,20],[5,10,10,1,20,20],[20,5,20,1,40,40]]

        player_types = PLAYER_TYPES
        player_strategies = ['third'] * 3 + ['dual rule']
        #player_weights=[np.random.randint(0,50,6).tolist() for i in xrange(4)]
        player_weights = [[1, 0, .5, 0, 3, 2], [2, 0, 2, 0, 1, 3], [
            2, 2, 2, 0, 2, 2], [1, 2, 2, .5, 20, 10]]

        with self.canvas:
            Num_Pieces = 21
            Num_Players = 4

            self.game = Game(dimension=board_size, num_players=Num_Players)
            self.helpers = []
            self.helper_timer = 0
            self.active_piece_timer = 0
            self.label = -1
            self.label_timer = 0
            self.board.size = (board_size * d, board_size * d)
            self.game_active = True
            if screen_mode == 'all_players':
                self.board.x = d * corner_offset[0]
                self.board.y = d * corner_offset[1]
            elif screen_mode == 'single_player':
                self.board.x = d * corner_offset[0]
                self.board.y = d * corner_offset[1]

            self.players = []
            for i in xrange(Num_Players):
                self.players += [Player(i,
                                        player_type=player_types[i],
                                        strategy=player_strategies[i],
                                        weights=player_weights[i])]
            self.current_move = [-1, []]

            # choose initial configurations for the pieces:
            ConfigInds = list(
                np.random.randint(
                    0,
                    len(Initial_Positions),
                    size=[Num_Players]))
            Positions = [0] * Num_Players
            Rotations = [0] * Num_Players
            Parities = [0] * Num_Players
            for playerID in xrange(Num_Players):
                if screen_mode == 'all_players':
                    offset = (0, 0)
                    rotate_initial_configuration = playerID
                elif screen_mode == 'single_player':
                    offset = (board_size, 0)
                    if Min_Size_Index == 0:
                        rotate_initial_configuration = 1
                    elif Min_Size_Index == 1:
                        rotate_initial_configuration = 0
                Positions[playerID], Rotations[playerID], Parities[playerID] = self.rotate_initial_configuration(
                    Initial_Positions[
                        ConfigInds[playerID]], Initial_Rotations[
                        ConfigInds[playerID]], Initial_Parities[
                        ConfigInds[playerID]], rotate_initial_configuration, dimension=size_in_blocks, offset=offset)

            self.pieces = []
            for i in xrange(Num_Pieces * Num_Players):
                # d=25.
                # position=(self.board.center[0]+i*d,
                #          self.board.center[1])
                pieceID = i % Num_Pieces + 1
                playerID = i / Num_Pieces
                rotation = Rotations[playerID][pieceID]
                parity = Parities[playerID][pieceID]
                piece = BlokusPiece(
                    pieceID=pieceID,
                    playerID=playerID,
                    rotation=rotation,
                    parity=parity)

                if screen_mode == 'all_players':
                    position = (
                        self.x + piece.d * Positions[playerID][pieceID][0],
                        self.y + piece.d * Positions[playerID][pieceID][1])
                elif screen_mode == 'single_player':
                    position = (
                        self.x +
                        piece.d *
                        Positions[playerID][pieceID][0] +
                        piece_offset[0] *
                        d,
                        self.y +
                        piece.d *
                        Positions[playerID][pieceID][1] +
                        piece_offset[1] *
                        d)
                piece.home = position
                wait_position = (WindowSize[0] + np.random.randint(WindowSize[0] + 2 * d, 1.5 * WindowSize[
                                 0] + 2 * d), np.random.randint(-WindowSize[1] / 2, 3 * WindowSize[1] / 2))
                piece.wait = wait_position
                if playerID == 0:
                    piece.pos = position
                    piece.setpoint = position
                else:
                    piece.pos = wait_position
                    piece.setpoint = wait_position
                self.pieces = self.pieces + [piece]
                self.add_widget(piece)

        self.instructions = TransformBubble()
        self.instructions.rotate_cw.bind(
            on_release=self.rotate_cw_active_piece)
        self.instructions.flip.bind(on_release=self.flip_active_piece)
        self.instructions.rotate_ccw.bind(
            on_release=self.rotate_ccw_active_piece)
        self.instructions.close.bind(on_release=self.close_instructions)
        self.instructions.commit.bind(on_release=self.add_piece)

        self.add_helpers()

    def rotate_initial_configuration(
        self,
        positions,
        rotations,
        parities,
        playerID,
        dimension=(
            42,
            42),
        offset=(
            0,
            0)):
        """
        rotate an initial configuration (which was configured for player 1), so that
        I can use it for a different player
        """
        pieces = [
            Piece(
                pieceID,
                playerID,
                rotation=rotations[pieceID],
                parity=parities[pieceID]) for pieceID in xrange(
                1,
                22)]

        new_positions = {}
        new_rotations = {}
        new_parities = {}
        playerID = playerID % 4

        for i in xrange(1, len(pieces) + 1):
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
        # update the gameboard according to the clock step dt

        # move the menu above the active piece so that it stays in sync with
        # the active piece
        if self.active_piece >= 0:
            self.instructions.y = self.pieces[
                self.active_piece].y + self.pieces[self.active_piece].height + 6
            self.instructions.center_x = self.pieces[
                self.active_piece].center_x
            if self.instructions.y + self.instructions.height > WindowSize[1]:
                self.instructions.y = WindowSize[1] - self.instructions.height
            if self.instructions.y < 0:
                self.instructions.y = 0
            if self.instructions.x < 0:
                self.instructions.x = 0
            if self.instructions.x + self.instructions.width > WindowSize[0]:
                self.instructions.x = WindowSize[0] - self.instructions.width

        moving = False
        for i in xrange(len(self.pieces)):
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
                        WindowSize[0] +
                        self.label.width,
                        1.5 *
                        WindowSize[0] +
                        self.label.width),
                    np.random.randint(
                        0,
                        WindowSize[1]))
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
                                (position[0] + corner_offset[0]) * d,
                                (position[1] + corner_offset[1]) * d)
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
            Size = 3 * d / 2.
            helper = HelperDot(
                size=(
                    Size,
                    Size),
                pos=(
                    (corner[0] + corner_offset[0] + .5) * d - Size / 2,
                    (corner[1] + corner_offset[1] + .5) * d - Size / 2))
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

        # print self.active_piece
        if self.players[self.game.current_playerID].player_type == 'human':
            position = self.pieces[self.active_piece].pos
        else:
            position = self.pieces[self.active_piece].setpoint

        position = (int(np.round(position[
                    0] / d - corner_offset[0])), int(np.round(position[1] / d - corner_offset[1])))
        # now position is the integer coordinates on the board
        self.remove_helpers()
        # attempt to place the piece on the gameboard:
        problem = self.game.place_piece(
            self.pieces[self.active_piece].piece, position)

        if problem == '':
            self.remove_widget(self.instructions)
            self.remove_widget(self.pieces[self.active_piece])
            self.board.place_piece(self.pieces[self.active_piece], position)
            self.pieces.pop(self.active_piece)
            self.active_piece = -1
            self.on_touch_up((0, 0))
            # print self.game

            if self.game.round == 0:
                self.add_helpers()

            for i in xrange(len(self.pieces)):
                if self.pieces[i].playerID == self.game.current_playerID:
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
                    for i in xrange(len(self.pieces)):
                        if self.pieces[
                                i].playerID == self.game.current_playerID:
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
                self.label = FlybyLabel(instance='game_over')
                self.label.pos = (np.random.randint(-WindowSize[0] - self.label.width, -self.label.width),
                                  np.random.randint(0, WindowSize[1]))
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
            self.label = FlybyLabel(instance='really')
            self.label.pos = (np.random.randint(-WindowSize[0] - self.label.width, -self.label.width),
                              np.random.randint(0, WindowSize[1]))
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
                # pass
                if self.pieces[i].playerID == self.game.current_playerID and self.pieces[
                        i].setpoint == self.pieces[i].home:
                    pos = self.pieces[i].pos
                    self.pieces[i].home = (
                        np.round(
                            pos[0] /
                            d -
                            corner_offset[0]) *
                        d +
                        corner_offset[0] *
                        d,
                        np.round(
                            pos[1] /
                            d -
                            corner_offset[1]) *
                        d +
                        corner_offset[1] *
                        d)


class BlokusApp(App):

    icon = './images/icon.png'
    title = 'Blokus'

    def build(self):
        game = BlokusGame()
        Clock.schedule_interval(game.update, 1.0 / 60.0)
        return game


if __name__ == '__main__':

    screen_mode = 'all_players'
    # screen_mode='single_player'
    view_mode = 'desktop'
    # view_mode='cell'
    PLAYER_TYPES = ['ai'] * 4

    arguments = sys.argv
    while len(arguments) > 1:
        argument = arguments.pop(0)
        if argument == 'display':
            value = arguments.pop(0)
            screen_mode = value
        if argument == 'players':
            value = int(arguments.pop(0))
            PLAYER_TYPES = ['human'] * value + ['ai'] * (4 - value)

    # initialize lists that contain information about where to put the pieces at
    # the start of the game. These pieces are efficiently packed in the space outside
    # the board. I computed several reasonable configurations, and saved them in the
    # initial_positions.dat file which is read in below to populate these initially
    # empty lists.
    Initial_Positions = []
    Initial_Rotations = []
    Initial_Parities = []

    # this assigns values to the lists Initial_Positions, etc...
    execfile("./initial_positions.py")
    Initial_Positions = Initial_Positions[screen_mode]
    Initial_Rotations = Initial_Rotations[screen_mode]
    Initial_Parities = Initial_Parities[screen_mode]

    # window should be fullscreen for final deployment
    if view_mode == 'cell':
        Window.fullscreen = True
    else:
        if screen_mode == 'all_players':
            Window.size = (650, 650)
        else:
            Window.size = (300, 600)
    WindowSize = Window.size
    print WindowSize
    Config.set('graphics', 'width', str(WindowSize[0]))
    Config.set('graphics', 'height', str(WindowSize[1]))
    Min_Size = min(WindowSize)
    Min_Size_Index = WindowSize.index(Min_Size)
    # a block size will be d

    # the window size will be square and contain an integer number of squares:

    if screen_mode == 'all_players':
        board_size = 20.
        window_size = 42.
        size_in_blocks = (window_size, window_size)
        corner_offset = [(window_size - board_size) / 2,
                         (window_size - board_size) / 2]
        d = float(np.floor(Min_Size / window_size))
    elif screen_mode == 'single_player':
        board_size = 20.
        piece_space_size = 17.
        if Min_Size_Index == 0:
            size_in_blocks = (board_size, board_size + piece_space_size)
        else:
            size_in_blocks = (board_size + piece_space_size, board_size)

        size_ratios = (
            WindowSize[0] /
            size_in_blocks[0],
            WindowSize[1] /
            size_in_blocks[1])
        min_size_ratio = min(size_ratios)
        limiting_index = size_ratios.index(min_size_ratio)
        d = float(
            np.floor(
                WindowSize[limiting_index] /
                size_in_blocks[limiting_index]))
        corner_offset = [0, 0]
        other_index = (limiting_index + 1) % 2
        corner_offset = [0] * 2
        piece_offset = [0] * 2
        for i in xrange(2):
            offset = float((WindowSize[i] - size_in_blocks[i] * d) / (2 * d))
            corner_offset[i] = offset
            piece_offset[i] = offset

        if Min_Size_Index == 0:
            corner_offset[1] = WindowSize[1] / \
                d - corner_offset[1] - board_size
        print Min_Size_Index
        print piece_offset
        print corner_offset
    else:
        raise RuntimeError('invalid screen mode')

    BlokusApp().run()

# python
# C:\Users\Brendon\Documents\PythonScripts\LearningPython\blokus\blokus.py

# to do:
    # saving games
    # scoring games
    # artificial intelligence rules
    # long runs
    # restarting game after its over
