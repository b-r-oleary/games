from piece import Piece

import numpy as np
import copy

def find_corners(board, playerID, game_round):
    """
    given an input board, and given a player_id, and game_round index,
    determine all of the corners that are valid connection points.

    inputs:
    board: (square numpy array) array containing the current pieces on the game board
    playerID: (int 0-3) id corresponding to each of the 4 players
    game_round: (int) number counting the current round in the game.
    """
    dimension = board.shape[0]
    start_points = [[0, 0], 
                    [0, dimension - 1],
                    [dimension - 1, dimension - 1], 
                    [dimension - 1, 0]]
    corners = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    edges = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if game_round == 0:
        available_corners = [start_points[playerID]]
    else:
        available_corners = []
        for i in xrange(dimension):
            for j in xrange(dimension):
                if board[i, j] == playerID + 1:
                    for corner in corners:
                        pos = (i + corner[0], j + corner[1])
                        if ((pos[0] in range(0, dimension)) and 
                            (pos[1] in range(0, dimension))):
                            available = True
                            if board[pos[0], pos[1]] == 0:
                                for edge in edges:
                                    pos2 = (pos[0] + edge[0], pos[1] + edge[1])
                                    if (pos2[0] in xrange(0, dimension)) and (
                                            pos2[1] in xrange(0, dimension)):
                                        if board[
                                                pos2[0], pos2[1]] == playerID + 1:
                                            available = False
                                            break
                            else:
                                available = False

                        else:
                            available = False

                        if available:
                            available_corners += [pos]
    return available_corners

def find_available_moves(game, pieces, playerID=-1, num=-1):
    """
    given a Game object "game", and an array of BlokusPiece objects "pieces",
    (and optional input playerID>0 to indicate whose turn it is if you dont
    want to default to playerID=game.current_playerID), then determine which
    moves are possible.

    num indicates how many moves to find. In principle, we only need to find
    one in order to indicate if the game can continue normally.
    """
    if playerID < 0:
        playerID = game.current_playerID

    corners = game.find_available_corners(playerID=playerID)

    # here are all of the available mating corners for each playerID
    #(i could get away with only the corners for the current player, but
    # getting all of them allows me to just how many blokus's are performed on a move
    # which could be part of a goodness metric for a strategy).

    # remove all of the other players pieces from the list
    pieces = [[i, pieces[i].piece]
              for i in xrange(len(pieces)) if pieces[i].playerID == playerID]
    moves = []

    for item in pieces:
        for rotation in xrange(0, 4):
            for parity in [-1, 1]:
                piece = item[1]
                ind = item[0]
                test_piece = Piece(
                    piece.pieceID,
                    piece.playerID,
                    rotation=rotation,
                    parity=parity)
                geo = test_piece.geometry
                Size = geo.shape
                for i in xrange(Size[0]):
                    for j in xrange(Size[1]):
                        for corner in corners:
                            test_position = (corner[0] - i, corner[1] - j)
                            new_board, problem = game.check_if_is_allowed(
                                test_piece, test_position)
                            if problem == '':
                                moves = moves + [{'playerID': piece.playerID,
                                                  'index': ind,
                                                  'pieceID': piece.pieceID,
                                                  'position': test_position,
                                                  'rotation': rotation,
                                                  'parity': parity}]
                            if (num > 0 and len(moves) >= num):
                                break
                        if (num > 0 and len(moves) >= num):
                            break
                    if (num > 0 and len(moves) >= num):
                        break
                if (num > 0 and len(moves) >= num):
                    break
            if (num > 0 and len(moves) >= num):
                break
        if (num > 0 and len(moves) >= num):
            break

    return moves

def determine_available_point_change(moves, game, pieces):
    """
    this is a function that is necessary for heuristic AI 
    rules 2 and 4 which rely on corner point expansion 
    or blocking of available corners.
    """

    # find the corners in the starting point:
    corners = []
    number_c = []
    for i in xrange(4):
        corner = game.find_available_corners(playerID=i)
        corners += [corner]
        number_c += [len(corner)]

    NativeCorners = [tuple(corn) for corn in corners[moves[0]['playerID']]]
    OppositionCorners = [corners[i] for i in xrange(
        len(corners)) if i != moves[0]['playerID']]
    OppositionCorners = [tuple(item)
                         for sublist in corners for item in sublist]

    blokus = []
    expansion = []
    for move in moves:
        native_corners = copy.deepcopy(NativeCorners)
        opposition_corners = copy.deepcopy(OppositionCorners)

        test_board = copy.deepcopy(game.board)  # np.zeros(game.board.shape)
        test_piece = Piece(
            move['pieceID'],
            move['playerID'],
            rotation=move['rotation'],
            parity=move['parity'])
        geo = test_piece.geometry
        Size = geo.shape
        position = move['position']
        for i in xrange(Size[0]):
            for j in xrange(Size[1]):
                if geo[i, j] == 1:
                    test_position = (position[0] + i, position[1] + j)
                    test_board[
                        test_position[0],
                        test_position[1]] = (
                        move['playerID'] + 1)
                    if test_position in native_corners:
                        ind = native_corners.index(test_position)
                        native_corners.pop(ind)
                    if test_position in opposition_corners:
                        ind = opposition_corners.index(test_position)
                        opposition_corners.pop(ind)

        new_corners = find_corners(
            test_board,
            game.current_playerID,
            game.round + 1)

        new_corners = [tuple(corn) for corn in new_corners]
        for corner in new_corners:
            if not(corner in native_corners):
                native_corners.append(corner)

        # print len(native_corners)
        blokus += [len(OppositionCorners) - len(opposition_corners)]
        expansion += [len(native_corners) - len(NativeCorners)]

    return {'add native': expansion, 'block opposition': blokus}


def find_number_of_patterns(board, playerID, patterns, position=-1, size=-1):
    board_size = board.shape
    if position < 0 or size < 0:
        size = board_size
        position = (0, 0)
        size = board.shape

    position = (position[0] - 1, position[1] - 1)
    size = (size[0] + 2, size[1] + 2)

    # first convert the board so that there are only empty spaces [0], player spaces [-1],
    # and opposition spaces [-2]
    board[board == (playerID + 1)] = -1
    board[board > 0] = -2
    # look for instances of these patterns (which are all the same but rotated
    # and flipped)
    cases = patterns
    instances = 0
    for case in cases:
        ncase = np.array(case)
        case_size = ncase.shape
        for i in xrange(size[0] - case_size[0] + 1):
            for j in xrange(size[1] - case_size[1] + 1):
                match = True
                for k in xrange(case_size[0]):
                    for m in xrange(case_size[1]):
                        temp_pos = (position[0] + i + k, position[1] + j + m)
                        # check that the temp_pos is in the right range:
                        if temp_pos[0] >= 0 and temp_pos[0] < board_size[0]\
                           and temp_pos[1] >= 1 and temp_pos[1] < board_size[1]:
                            # check if there is a match:
                            if board[temp_pos[0], temp_pos[1]] != ncase[k, m]:
                                match = False
                                break
                        else:
                            match = False
                            break
                    if not match:
                        break
                if match:
                    instances += 1
    return instances


def find_bridge_instances(board, playerID, position=-1, size=-1):
    """
    given a board, find and count the number of instances of "bridging" - this means
    that a player of one color has an opportunity to cross the boundary of another
    """
    patterns = [[[0, -2], [-2, -1]], [[-2, 0], [-1, -2]],
                [[-2, -1], [0, -2]], [[-1, -2], [-2, 0]]]
    bridges = find_number_of_patterns(
        board, playerID, patterns, position=position, size=size)
    return bridges


def find_edge_sharing(board, playerID, position=-1, size=-1):
    """
    given a board, count the number of instances of edge sharing between our
    pieces and other pieces
    """
    patterns = [[[-1, -2]], [[-1], [-2]], [[-2, -1]], [[-2], [-1]]]
    edges = find_number_of_patterns(
        board,
        playerID,
        patterns,
        position=position,
        size=size)
    return edges