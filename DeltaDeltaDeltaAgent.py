import chess


class DeltaDeltaDeltaAgent:
    """
    Your agent class. Please rename this to {TeamName}Agent, and this file to {TeamName}.py
    """
    depth = 3
    current_move = 1
    cache = {}

    def __init__(self, is_white):
        """
        Constructor, initialize your fields here.
        :param is_white: Initializes the color of the agent.
        """
        self.is_white = is_white

    @staticmethod
    def get_team_name():
        """
        Report your team name. Used for scoring purposes.
        """
        return "DeltaDeltaDelta"

    def get_board_value(self, board, return_difference=True) -> int:
        return sum(get_piece_utility(board.piece_at(square), return_difference)
                   if board.piece_at(square) is not None else 0
                   for square in chess.SQUARES
                   )

    def exchange_heuristic(self, board):
        score = 0

        for square in chess.SQUARES:
            if board.piece_at(square) is not None:  # Have a piece at this square
                if board.piece_at(square).color == self.is_white:  # Is our piece
                    if board.piece_at(square).piece_type != chess.KING:  # Not a king
                        attackers = board.attackers(not self.is_white, square)
                        protectors = board.attackers(self.is_white, square)
                        if len(attackers) > 0:  # Piece is being attacked
                            if len(protectors) >= len(attackers):  # We will win the attack by number of pieces
                                score += 1
                            else:
                                score -= 1

        if self.is_white:
            return score * self.get_heuristic_multiplier(board, "exchange_heuristic")
        else:
            return -score * self.get_heuristic_multiplier(board, "exchange_heuristic")

    def pawn_advancment_heuristic(self, board):
        value = 0
        for square in chess.SQUARES:
            if board.piece_at(square) is not None:
                if board.piece_at(square).color == self.is_white:
                    if board.piece_at(square).piece_type == chess.PAWN:
                        if self.is_white:
                            value += chess.square_rank(square)
                        else:
                            value += 8 - chess.square_rank(square)

        if not self.is_white:
            value = -value

        return value * self.get_heuristic_multiplier(board, "pawn_advancment_heuristic")

    def checkmate_heuristic(self, board):
        if board.is_checkmate():
            if board.result() == "1-0" and self.is_white:
                return 1000000
            elif board.result() == "0-1" and not self.is_white:
                return -1000000
            elif not self.is_white:
                return 1000000
            else:
                return -1000000
        return 0

    def piece_development_heuristic(self, board):
        value = 4
        for square in chess.SQUARES:
            piece = board.piece_at(square).lower()
            if piece is not None:
                # White back row
                if self.is_white and square < 8:
                    if piece == 'n' or piece == 'b':
                        value = value - 1
                # Black back row
                elif not self.is_white and square > 55:
                    if piece == 'n' or piece == 'b':
                        value = value - 1

        if not self.is_white:
            value = value * -1
        return value * self.get_heuristic_multiplier(board, "piece_development_heuristic")

    def opposing_king_heuristic(self, board) -> int:
        possible_king_moves = 0

        for square in chess.SQUARES:
            if board.piece_at(square) is not None:  # Have a piece at this square
                if board.piece_at(square).color != self.is_white:  # Is not our piece
                    if board.piece_at(square).piece_type == chess.KING:  # Is their king
                        possible_moves = board.legal_moves
                        for move in possible_moves:
                            if move.from_square == square:
                                possible_king_moves += 1

                        return possible_king_moves * (1 if self.is_white else -1) * \
                               self.get_heuristic_multiplier(board, "opposing_king")  # Break from the for loop

    def game_utility_heuristic(self, board) -> int:
        """
        This heuristic evaluates the total points on the board, which is positive
        if white is leading, or negative if black is leading
      """
        return self.get_heuristic_multiplier(board, "game_utility") * self.get_board_value(board)

    def get_heuristic_multiplier(self, board, heuristic_name) -> int:
        """
        This function is called by each heuristic function to get the multiplier it
        needs, based on the current state of the game
      """
        heuristics = {}
        heuristics["exchange_heuristic"] = [1, 5, 5]  # Early, Mid, Late Game
        heuristics["pawn_advancment_heuristic"] = [0.2, 0.1, 0.2]  # Early, Mid, Late Game
        heuristics["piece_development_heuristic"] = [1, 0, 0]  # Early, Mid, Late Game
        heuristics["opposing_king"] = [1, 10, 20]
        heuristics["game_utility"] = [5, 5, 6]  # Early, Mid, Late Game

        game_state = 0

        # Determine current game state
        if self.get_board_value(board, False) < 50:  # If totals of both sides are less than 50
            game_state = 2
        elif self.current_move > 10:  # If 10+ moves have been played
            game_state = 1

        weights = heuristics[heuristic_name]

        return weights[game_state]

    def combined_heuristic(self, board):
        """
        Determine whose favor the board is in, and by how much.
        Positive values favor white, negative values favor black.

        :param board:
        :return: Returns the estimated utility of the board state.
        """
        # Evaluate scores of each piece
        value = 0

        value += self.exchange_heuristic(board)
        value += self.pawn_advancment_heuristic(board)
        value += self.checkmate_heuristic(board)
        value += self.opposing_king_heuristic(board)
        value += self.game_utility_heuristic(board)

        # If this is a draw, value is 0 (same for both players)

        if board.can_claim_draw():
            value = 0

        return value

    def make_move(self, board):
        """
        Determine the next move to make, given the current board.
        :param board: The chess board
        :return: The selected move
        """
        global_score = -1e8 if self.is_white else 1e8
        chosen_move = None

        for move in board.legal_moves:
            board.push(move)

            local_score = self.minimax(board, self.depth - 1, not self.is_white, -1e8, 1e8)
            self.cache[hash_board(board, self.depth - 1, not self.is_white)] = local_score

            if self.is_white and local_score > global_score:
                global_score = local_score
                chosen_move = move
            elif not self.is_white and local_score < global_score:
                global_score = local_score
                chosen_move = move

            board.pop()
            self.current_move += 2  # Accounts for the other players moves

        return chosen_move

    def minimax(self, board, depth, is_maxing_white, alpha, beta):
        """
        Minimax implementation with alpha-beta pruning.

        Source: https://github.com/devinalvaro/yachess

        :param board: Chess board
        :param depth: Remaining search depth
        :param is_maxing_white: Whose score are we maxing?
        :param alpha: Alpha-beta pruning value
        :param beta: Alpha-beta pruning value
        :return: The utility of the board state
        """
        # Check if board state is in cache
        if hash_board(board, depth, is_maxing_white) in self.cache:
            return self.cache[hash_board(board, depth, is_maxing_white)]

        # Check if game is over or we have reached maximum search depth.
        if depth == 0 or not board.legal_moves:
            self.cache[hash_board(board, depth, is_maxing_white)] = self.combined_heuristic(board)
            return self.cache[hash_board(board, depth, is_maxing_white)]

        # General case
        best_score = -1e8 if is_maxing_white else 1e8
        for move in board.legal_moves:
            board.push(move)

            local_score = self.minimax(board, depth - 1, not is_maxing_white, alpha, beta)
            self.cache[hash_board(board, depth - 1, not is_maxing_white)] = local_score

            if is_maxing_white:
                best_score = max(best_score, local_score)
                alpha = max(alpha, best_score)
            else:
                best_score = min(best_score, local_score)
                beta = min(beta, best_score)

            board.pop()

            if beta <= alpha:
                break
        self.cache[hash_board(board, depth, is_maxing_white)] = best_score
        return self.cache[hash_board(board, depth, is_maxing_white)]


def hash_board(board, depth, is_maxing_white):
    """
    Get a representation of the system that we can cache.
    """
    return str(board) + ' ' + str(depth) + ' ' + str(is_maxing_white)


def get_piece_utility(piece, return_difference=True):
    """
    Get the utility of a piece.
    :return: Returns the standard chess score for the piece, positive if white, negative if black.
    """
    piece_symbol = piece.symbol()
    is_white = not piece_symbol.islower()

    lower = piece_symbol.lower()

    score = (1 if is_white else -1) if return_difference else 1

    if lower == 'p':
        score *= 1
    elif lower == 'n':
        score *= 3
    elif lower == 'b':
        score *= 3
    elif lower == 'r':
        score *= 5
    elif lower == 'q':
        score *= 9
    elif lower == 'k':
        score *= 1_000_000
    return score
