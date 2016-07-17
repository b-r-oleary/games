import numpy as np

# here are the names of the colors in order in
# which they will be played.
COLORS = ['blue', 'red', 'green', 'yellow']

# here are representations all of the allowed pieces:
PIECES = {1: [[1]],
          2: [[1, 1]],
          3: [[1, 1, 1]],
          4: [[1, 1], [0, 1]],
          5: [[1, 1, 1, 1]],
          6: [[1, 1, 0], [0, 1, 1]],
          7: [[1, 1, 1], [0, 1, 0]],
          8: [[1, 1, 1], [0, 0, 1]],
          9: [[1, 1], [1, 1]],
          10: [[1, 1, 1, 1, 1]],
          11: [[1, 1, 1, 1], [0, 0, 0, 1]],
          12: [[1, 1, 1, 0], [0, 0, 1, 1]],
          13: [[1, 1, 1, 1], [0, 0, 1, 0]],
          14: [[1, 1, 1], [0, 0, 1], [0, 0, 1]],
          15: [[1, 1, 0], [0, 1, 1], [0, 0, 1]],
          16: [[1, 1, 0], [0, 1, 1], [0, 1, 0]],
          17: [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
          18: [[1, 1, 1], [1, 1, 0]],
          19: [[1, 1, 1], [0, 1, 0], [0, 1, 0]],
          20: [[1, 1, 1], [1, 0, 1]],
          21: [[1, 1, 0], [0, 1, 0], [0, 1, 1]]}


class Piece(object):
    """
    this class defines a blokus piece - not the widget,
    but rather the information that characterizes a piece.

    methods:
    rotate - rotate this blokus piece
    flip   - replace this piece about a left-right reflection plane
    reset_orientation - reset to the initial orientation before rotating and flipping
    place_on_board    - given a numpy array board, and a specified position,
    		 place the piece on the board by setting the positions that are occupied by this
    		 piece to -1.
    """

    def __init__(self, pieceID, playerID, rotation=0, parity=1):
        """
        inputs:
        pieceID: (int) integer corresponding the the blokus piece
                       found in the PIECES dictionary
        playerID: (int) integer between 0-3 corresponding to the
                       player to whom this piece belongs
        rotation: (int) rotation angle state between 0-3
        parity:   (int, -1 or 1) parity of the piece
        """

        self._geometry = np.array(PIECES[pieceID])
        self.geometry  = np.array(PIECES[pieceID])
        self.rotation  = 0
        self.parity    = 1
        self.pieceID   = pieceID
        self.color     = COLORS[playerID]
        self.playerID  = playerID

        if parity == -1:
            self.flip()

        if not(rotation == 0):
            self.rotate(rotation=rotation)

    def rotate(self, rotation=1):
        rotation = rotation % 4
        self.geometry = np.rot90(self.geometry, k=rotation)
        self.rotation = (self.rotation + rotation) % 4

    def flip(self):
        self.parity = (-1) * (self.parity)
        self.geometry = np.fliplr(self.geometry)
        # since the flip goes first and since the the flip operator does not
        # commute with the rotation operator, and since this flip could come after the
        # rotation, then I need to figure out what the right rotation value is, and
        # set that value to self.rotation.
        new_geo = np.array(PIECES[self.pieceID])
        if self.parity == -1:
            new_geo = np.fliplr(new_geo)
        for k in xrange(4):
            new_list = new_geo.tolist()
            old_list = self.geometry.tolist()
            if new_list == old_list:
                self.rotation = k
                break
            else:
                new_geo = np.rot90(new_geo, k=1)

    def reset_orientation(self, rotation=0, parity=1):
        self.geometry = self._geometry
        if parity == -1:
            self.flip()
        self.rotate(rotation=rotation)

    def __len__(self):
        return np.sum(np.sum(self.geometry))

    def __repr__(self):
        return (str(self.pieceID) + ':' + str(self.playerID) +
                ':' + str(self.rotation) + ':' + str(self.parity))

    def shape(self):
        return self.geometry.shape

    def place_on_board(self, board, position):
        for i in xrange(self.geometry.shape[0]):
            for j in xrange(self.geometry.shape[1]):
                if self.geometry[i, j] == 1:
                    board[i, j] = -1
        return board