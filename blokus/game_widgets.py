from __future__ import division

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

from game import Game
from piece import Piece

class Block(Widget):
    """
    this is a single block and contains the image of the block. the blokus
    pieces are made up of multiple blocks. This has an input property "playerID"
    which is an integer 0-3 which corresponds to the player color.
    """

    playerID = NumericProperty(0)

    def __init__(self, d=0, **kwargs):
        super(Block, self).__init__(**kwargs)

        with self.canvas:
            # here is the path indicating the location of the block images
            colors = ['blue', 'red', 'green', 'yellow']
            color = colors[self.playerID]
            self.image = './blokus/images/block_' + color + '.png'
            # d is the fixed size of a block in pixels
            self.size = tuple([int(d)] * 2)
            self.rect = Rectangle(source=self.image,
                                  pos=self.center,
                                  size=self.size)

        # manually indicate that we need to update the image size and location size
        # if we call the widget to move or be resized.
        self.bind(pos=self.update_rect,
                  size=self.update_rect),

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class BlokusPiece(Widget):
    """
    This object defines a Blokus piece widget
    which includes as fields a "Piece" object
    that includes the piece geometry, and a list
    of "Block" widgets that instantiates that
    geometry on the board.

    methods:
    update_blocks: move the blocks that make up the piece
        so that they have the right relative positions.
    update: Move the piece. If the piece is grabbed, move with
        the cursor. If the piece is not grabbed, go to the setpoint
        if it is not already there. The setpoint can be either a home
        or a local grid point.
    on_touch_down: Identifies when we are grabbing the piece
    on_touch_up: Identifies when we release a piece.
    on_touch_move: Identifies when we are dragging a piece.
    flip: Flips piece by calling the Piece.flip method
    rotate: Rotates piece by calling the Piece.rotate method.
    """
    pieceID = NumericProperty(0)
    playerID = NumericProperty(0)
    rotation = NumericProperty(0)
    parity = NumericProperty(1)

    def __init__(self, d=0, 
                 corner_offset=(0,0),
                 move_increment=.2,
                 stop_tolerance=.1,
                 **kwargs):
        super(BlokusPiece, self).__init__(**kwargs)

        self.piece = Piece(
            self.pieceID,
            self.playerID,
            rotation=self.rotation,
            parity=self.parity)

        self.d = int(d)
        self.corner_offset = corner_offset
        self.increment = move_increment
        self.tolerance = stop_tolerance

        with self.canvas:
            self.blocks = []
            self.rel_pos = []
            self.grabbed = False  # use this to indicate whether or not i'm holding the piece
            self.enabled = True
            self.go_to_setpoint = False
            self.home = (0, 0)
            self.setpoint = (0, 0)
            self.wait = (0, 0)
            size = self.piece.geometry.shape
            self.size = (self.d * size[0], self.d * size[1])
            for i in range(size[0]):
                for j in range(size[1]):
                    if self.piece.geometry[i, j] == 1:
                        block = Block(playerID=self.playerID, d=self.d)
                        self.blocks = self.blocks + [block]

        self.bind(pos=self.update_blocks)

    def update_blocks(self, *args):
        """
        moves the blocks that make up the blokus piece
        """
        index = 0
        Size = self.piece.geometry.shape
        self.size = (self.d * Size[0], self.d * Size[1])
        for i in xrange(Size[0]):
            for j in xrange(Size[1]):
                if self.piece.geometry[i, j] == 1:
                    self.blocks[index].pos = (
                        i * self.d + self.pos[0], j * self.d + self.pos[1])
                    index += 1

    def update(self):
        """
        this function updates on the clock. This is mostly providing a "snap to grid" feature
        """
        if not(self.grabbed):
            current_position = self.pos
            if self.go_to_setpoint:
                final_position = (
                    float(self.setpoint[0]), 
                    float(self.setpoint[1]))
            else:
                final_position = (
                        float(np.round((self.pos[0]) / self.d - self.corner_offset[0]) * self.d + (self.corner_offset[0] * self.d)),
                        float(np.round((self.pos[1]) / self.d - self.corner_offset[1]) * self.d + (self.corner_offset[1] * self.d)))

            direction = (
                final_position[0] -
                current_position[0],
                final_position[1] -
                current_position[1])

            # how far towards the final position should it go in one step
            changed_position = (
                current_position[0] +
                self.increment *
                direction[0],
                current_position[1] +
                self.increment *
                direction[1])

            self.pos = changed_position
            
            if self.go_to_setpoint:
                distance = float(np.sqrt(direction[0]**2 + direction[1]**2))
                if distance <= self.tolerance:
                    self.go_to_setpoint = False

    def on_touch_down(self, touch):
        if self.enabled:
            Touch = False
            for block in self.blocks:
                if block.collide_point(*touch.pos):
                    Touch = True
                    break
            if Touch:
                touch.grab(self)
                self.grab_point = (
                    touch.pos[0] - self.center_x,
                    touch.pos[1] - self.center_y)
                self.grabbed = True
                return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.grabbed = False
            return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.center = (
                touch.x - self.grab_point[0],
                touch.y - self.grab_point[1])

    def flip(self):
        self.piece.flip()

    def rotate(self, rotation=1):
        self.piece.rotate(rotation=rotation)


class HelperDot(Widget):
    """
    This is a little star widget
    that shows you the available corners
    at which you can place a piece if it
    is your turn. These only show up when you
    need help.
    """
    pass


class TransformBubble(Bubble):
    """
    This is a floating menu that enables human players
    to manipulate the orientation of a piece, and to commit
    a move.
    """
    rotate_cw = ObjectProperty(None)
    rotate_ccw = ObjectProperty(None)
    flip = ObjectProperty(None)
    close = ObjectProperty(None)
    commit = ObjectProperty(None)


class GameBoard(Widget):
    """
    This is the widget that represents the GameBoard.
    This does not contain information about the game,
    but rather just contains an image of the GameBoard
    and also contains all of the piece widgets that have
    already been placed on the board.
    """

    def place_piece(self, piece, position,
                    d, corner_offset):
        with self.canvas:
            try:
                self.pieces += [piece]
            except:
                self.pieces = [piece]
            piece.pos = (
                (position[0] + corner_offset[0]) * d,
                (position[1] + corner_offset[1]) * d)
            piece.enabled = False
            self.add_widget(piece)


class FlybyLabel(Widget):
    """
    This is a widget that flies onto the screen when either
    you attempt an illegal move (which says "really?"), or when
    the game ends (which says "game over")
    """
    instance = StringProperty('really')

    def __init__(self, d=0, **kwargs):
        super(FlybyLabel, self).__init__(**kwargs)
        self.setpoint = (0, 0)
        self.go_to_setpoint = False
        self.size = (15 * d, 15 * d)
        with self.canvas:
            self.rect = Image(
                source=(
                    './blokus/images/' +
                    self.instance +
                    '.png'),
                keep_ratio=True,
                allow_stretch=True)

        self.bind(pos=self.update_rect,
                  size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update(self):
        if self.go_to_setpoint:
            iteration = .2
            pos = self.pos
            new_pos = [(iteration * (self.setpoint[i] - pos[i]) + pos[i])
                       for i in xrange(len(self.pos))]
            distance = np.sqrt((pos[0] - new_pos[0]) **
                               2 + (pos[1] - new_pos[1])**2)
            self.pos = new_pos
            if distance < .001:
                self.go_to_setpoint = False