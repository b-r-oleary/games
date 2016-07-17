import numpy as np
import copy

from game_methods import find_corners

class Game(object):
    """
	This object keeps track of the Blokus game:

	methods:
	increment_turn: increments the playerID, and the round counter.
	find_available_corners: for the specified playerID, find corners
		that represent valid connection points for a piece.
	check_if_is_allowed: given a piece and a piece position on the board
		determine if the move is allowed or not. This function contains
		most of the rules of Blokus
	place_piece: given a piece and a valid position, place the piece
		on the current game board, and increment the turn.
    """

    def __init__(self, dimension=20, num_players=4):
        self.board = np.zeros([dimension, dimension])
        self.round = 0
        self.num_players = num_players
        self.current_playerID = 0
        self.dimension = int(dimension)
        self.history = []

    def __repr__(self):
        string = ''
        for i in xrange(self.dimension):
            for j in xrange(self.dimension):
                string += (str(int(self.board[i, j])) + ' ')
            string += '\n'
        return string

    def increment_turn(self):
        if self.current_playerID == self.num_players - 1:
            self.current_playerID = 0
            self.round = self.round + 1
        else:
            self.current_playerID = self.current_playerID + 1

    def find_available_corners(self, playerID=-1):
        if playerID < 0:
            playerID = self.current_playerID
        Available_Corners = find_corners(self.board, playerID, self.round)
        return Available_Corners

    def check_if_is_allowed(self, piece, piece_position):

        start_points = [[0, 0], [0, self.dimension -
                                 1], [self.dimension -
                                      1, self.dimension -
                                      1], [self.dimension -
                                           1, 0]]
        corners = [[-1, -1], [-1, 1], [1, -1], [1, 1]]
        edges = [[1, 0], [-1, 0], [0, 1], [0, -1]]
        new_board = copy.deepcopy(self.board)

        if self.current_playerID == piece.playerID:
            playerID = self.current_playerID
            corner_touch = 0

            geo = piece.geometry
            Size = geo.shape

            problem = ''  # if there is a problem, it will show up here
            # problem indicates if a move violates a rule of the game,
            # and if so indicates why

            for i in xrange(Size[0]):
                for j in xrange(Size[1]):
                    if geo[i, j] == 1 and problem == '':
                        # the positioin of one of the blocks is at X:
                        X = [piece_position[0] + i, piece_position[1] + j]
                        # check that this is on the board:
                        InRange = (
                            ((X[0] < self.dimension) and (
                                X[0] >= 0)) and (
                                (X[1] < self.dimension) and (
                                    X[1] >= 0)))
                        if InRange:
                            # check that this location is not occupied:
                            if new_board[X[0], X[1]] == 0:
                                new_board[X[0], X[1]] = -1
                                if self.round == 0:
                                    if X == start_points[playerID]:
                                        corner_touch = 1
                                else:
                                    # check that it is touching at least 1
                                    # corner:
                                    CornerTouch = []
                                    for corner in corners:
                                        pos = (
                                            X[0] + corner[0], X[1] + corner[1])
                                        if (pos[0] in xrange(0, self.dimension)) and (
                                                pos[1] in xrange(0, self.dimension)):
                                            CornerTouch += [
                                                (new_board[pos[0], pos[1]] == playerID + 1)]
                                    if np.any(CornerTouch):
                                        corner_touch = 1

                                    EdgeTouch = []
                                    for edge in edges:
                                        pos = (X[0] + edge[0], X[1] + edge[1])
                                        if (pos[0] in xrange(0, self.dimension)) and (
                                                pos[1] in xrange(0, self.dimension)):
                                            touch = (
                                                new_board[
                                                    pos[0], pos[1]] == playerID + 1)
                                            EdgeTouch += [touch]
                                            if touch:
                                                problem = 'this piece has a shared edge with another piece'
                                                break
                                    if np.any(EdgeTouch):
                                        problem = 'this piece has a shared edge with another piece'
                            else:
                                problem = 'this piece overlaps with an existing piece'
                        else:
                            problem = 'the piece is not completely on the board'

                    if problem != '':
                        break
                if problem != '':
                    break

            if corner_touch == 0 and problem == '':
                if self.round == 0:
                    problem = 'the piece must touch the right corner of the board'
                else:
                    problem = 'the piece must be adjacent to a piece of the same color'

            if problem == '':
                # the piece has been placed successfully, place it on the board,
                # increment the turn, and make a log of the turn
                new_board[new_board == -1] = playerID + 1
            else:
                new_board[new_board == -1] = 0
        else:
            problem = ('you cant place a piece it is player ' +
                       str(self.current_playerID + 1) + 's turn.')
            # print problem
        return new_board, problem

    def place_piece(self, piece, position):

        new_board, problem = self.check_if_is_allowed(piece, position)

        if problem == '':
            # if the piece has been placed successfully, place it on the board,
            # increment the turn, and make a log of the turn.
            self.history += [{'playerID': piece.playerID,
                              'pieceID': piece.pieceID,
                              'rotation': piece.rotation,
                              'parity': piece.parity,
                              'position': position}]
            self.board = new_board
            self.increment_turn()

        return problem