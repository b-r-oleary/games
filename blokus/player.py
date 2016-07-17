import numpy as np
import copy

from game_methods import find_available_moves
from game_methods import determine_available_point_change
from game_methods import find_edge_sharing
from game_methods import find_bridge_instances

from piece import Piece

class Player(object):
    """
    this class describes the player/artificial intelligence. The input parameters describe
    the parameters necessary to build the algorithm
    """

    def __init__(self, playerID, player_type='human',
                 strategy='random', weights=[5., 1., 1, .5, 5, 10]):
        colors = ['blue', 'red', 'green', 'yellow']
        self.playerID = playerID
        self.player_type = player_type
        self.strategy = strategy
        self.color = colors[self.playerID]
        self.weights = weights

    def __repr__(self):
        return ('player ' + str(self.playerID + 1) + ': ' + self.player_type)

    def make_move(self, game, pieces):
        if self.player_type != 'human':
            # first find all available moves to make
            moves = find_available_moves(game, pieces)
            # print moves
            #raise RuntimeError('')
            if self.strategy == 'random':
                # choose one move at random
                move = moves[np.random.randint(0, len(moves))]
            elif self.strategy == 'markov rule':
                active_rules = [
                    self.rule_1,
                    self.rule_2,
                    self.rule_3,
                    self.rule_4,
                    self.rule_5,
                    self.rule_6]
                data = determine_available_point_change(moves, game, pieces)
                metric = np.zeros([len(moves)])
                metrics = []
                for i in xrange(len(active_rules)):
                    current_metric = active_rules[i](moves, game, pieces, data)
                    scaled_metric = self.weights[
                        i] * (1 + .2 * np.random.normal(0, 1)) * current_metric
                    metric = metric + scaled_metric
                    metrics += [current_metric.tolist()]
                metric = metric.tolist()
                metric = [int(item) for item in metric]
                Max = max(metric)
                Inds = [i for i in xrange(len(metric)) if metric[i] == Max]
                Ind = Inds[np.random.randint(0, len(Inds))]
                move = moves[Ind]
                move_metric = [m[Ind] for m in metrics]
                print move_metric
            elif self.strategy == 'third':
                active_rules = [
                    self.rule_1,
                    self.rule_2,
                    self.rule_3,
                    self.rule_4,
                    self.rule_5,
                    self.rule_6]
                data = determine_available_point_change(moves, game, pieces)
                metric = np.ones([len(moves)])
                metrics = []
                for i in xrange(len(active_rules)):
                    current_metric = active_rules[i](moves, game, pieces, data)
                    current_metric[current_metric <= 0] = 0
                    current_metric += 1
                    scaled_metric = current_metric**(self.weights[i])
                    metric = metric * scaled_metric
                    metrics += [current_metric.tolist()]
                metric[np.isnan(metric)] = 0
                metric = metric.tolist()
                metric = [int(item) for item in metric]
                Max = max(metric)
                Inds = [i for i in xrange(len(metric)) if metric[i] == Max]
                Ind = Inds[np.random.randint(0, len(Inds))]
                move = moves[Ind]
                move_metric = [m[Ind] for m in metrics]
                print move_metric
            elif self.strategy == 'dual rule':
                # first find several reasonably good moves by the same method as the
                # markov rule:

                active_rules = [
                    self.rule_1,
                    self.rule_2,
                    self.rule_3,
                    self.rule_4,
                    self.rule_5,
                    self.rule_6]

                new_game = copy.deepcopy(game)
                new_pieces = copy.deepcopy(pieces)

                data = determine_available_point_change(
                    moves, new_game, new_pieces)
                metric = np.zeros([len(moves)])
                metrics = []
                for i in xrange(len(active_rules)):
                    current_metric = active_rules[i](
                        moves, game, new_pieces, data)
                    scaled_metric = self.weights[
                        i] * (1 + .2 * np.random.normal(0, 1)) * current_metric
                    metric = metric + scaled_metric
                    metrics += [current_metric.tolist()]
                metric = metric.tolist()
                metric = [item for item in metric]
                Inds = np.argsort(metric).tolist()
                Inds.reverse()
                Num = 3
                Inds = Inds[0:Num]
                moves = [moves[ind] for ind in Inds]
                metric = [metric[ind] for ind in Inds]
                index = -1
                for move in moves:
                    index += 1
                    new_game = copy.deepcopy(game)
                    new_pieces = copy.deepcopy(pieces)
                    first_piece = Piece(
                        move['pieceID'],
                        move['playerID'],
                        rotation=move['rotation'],
                        parity=move['parity'])
                    new_game.place_piece(first_piece, move['position'])
                    new_game.current_playerID = move['playerID']
                    new_pieces.pop(move['index'])

                    new_moves = find_available_moves(new_game, new_pieces)

                    if len(new_moves) != 0:
                        new_data = determine_available_point_change(
                            new_moves, new_game, new_pieces)
                        new_metric = np.zeros([len(new_moves)])

                        for i in xrange(len(active_rules)):
                            current_metric = active_rules[i](
                                new_moves, new_game, new_pieces, new_data)
                            scaled_metric = self.weights[
                                i] * (1 + .2 * np.random.normal(0, 1)) * current_metric
                            new_metric = new_metric + scaled_metric

                        new_metric = new_metric.tolist()
                        metric[index] = metric[index] * sum(new_metric)

                Max = max(metric)
                Inds = [i for i in xrange(len(metric)) if metric[i] == Max]
                Ind = Inds[np.random.randint(0, len(Inds))]
                move = moves[Ind]

                print metric[Ind]

            else:
                raise RuntimeError('unknown strategy type.')
            # now that I have chosen my move, make it
        else:
            move = []
        return move

    def rule_1(self, moves, game, pieces, data):
        """
        try to put down larger pieces first
        return float [0,1] for each move in a list
        """
        metric = []
        for i in xrange(len(moves)):
            metric += [(len(pieces[moves[i]['index']].piece))]
        return np.array(metric)

    def rule_2(self, moves, game, pieces, data):
        """
        try to increase own connection points as much as possible
        """
        metric = data['add native']
        return np.array(metric)

    def rule_3(self, moves, game, pieces, data):
        """
        keep away from the walls
        """
        dimension = game.board.shape[0]
        half_dim = np.floor(dimension / 2.)
        board_center = (half_dim, half_dim)

        centered = []
        for move in moves:
            piece_pos = move['position']
            size = pieces[move['index']].piece.geometry.shape
            piece_pos = (
                piece_pos[0] + size[0] / 2.,
                piece_pos[1] + size[1] / 2.)
            dist = np.sqrt((piece_pos[0] - board_center[0])
                           ** 2 + (piece_pos[1] - board_center[1])**2)
            centered += [half_dim - dist]

        return np.array(centered)

    def rule_4(self, moves, game, pieces, data):
        """
        try to block as many opponents points as possible
        """
        metric = data['block opposition']
        return np.array(metric)

    def rule_5(self, moves, game, pieces, data):
        """
        try to share edge space with opponents as much as possible
        """
        metric = []
        test_board = copy.deepcopy(game.board)
        for move in moves:
            t_board = test_board
            t_piece = Piece(
                move['pieceID'],
                move['playerID'],
                rotation=move['rotation'],
                parity=move['parity'])
            position = move['position']
            t_board = t_piece.place_on_board(t_board, position)
            after = find_edge_sharing(
                t_board,
                game.current_playerID,
                position=move['position'],
                size=t_piece.geometry.shape)
            # using before and after, encourages starting and crossing bridges
            metric += [after]
        return np.array(metric)

    def rule_6(self, moves, game, pieces, data):
        """
        try to create bridges across other players gaps if at all possible.
        """
        metric = []
        test_board = copy.deepcopy(game.board)
        for move in moves:
            t_board = test_board
            t_piece = Piece(
                move['pieceID'],
                move['playerID'],
                rotation=move['rotation'],
                parity=move['parity'])
            position = move['position']
            before = find_bridge_instances(
                t_board,
                game.current_playerID,
                position=move['position'],
                size=t_piece.geometry.shape)
            t_board = t_piece.place_on_board(t_board, position)
            after = find_bridge_instances(
                t_board,
                game.current_playerID,
                position=move['position'],
                size=t_piece.geometry.shape)
            # using before and after, encourages starting and crossing bridges
            metric += [before + after]
        return np.array(metric)