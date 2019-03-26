import chess.pgn
import itertools
import io


tier_1_confidence = 0.99
tier_2_confidence = 0.95
tier_2_minimum_confidence = 0.025
tier_3_minimum_confidence = 0.01
one_hot_encoded_mappings = 'O12345678BKNQRxabcdefgh-'


class Ply:
    def __init__(self, value):
        self.value = value

    numbers = ['1', '2', '3', '4', '5', '6', '7', '8']
    lowercase_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    capital_letters = ['B', 'K', 'N', 'Q', 'R']

    def is_legal_format(self):
        nums = Ply.numbers
        lowers = Ply.lowercase_letters
        caps = Ply.capital_letters

        ply = self.value

        def is_legal_2_chars():
            def pawn_move():
                char_1_legal = ply[0] in lowers
                char_2_legal = ply[1] in nums

                if char_1_legal and char_2_legal:
                    return True
                return False

            if pawn_move():
                return True
            return False

        def is_legal_3_chars():
            def piece_move():
                char_1_legal = ply[0] in caps
                char_2_legal = ply[1] in lowers
                char_3_legal = ply[2] in nums

                if char_1_legal and char_2_legal and char_3_legal:
                    return True
                return False

            shortside_castle = ply == 'O-O'

            if piece_move() or shortside_castle:
                return True
            return False

        def is_legal_4_chars():
            def piece_takes():
                char_1_legal = ply[0] in caps
                char_2_legal = ply[1] == 'x' or ply[1] in nums or ply[1] in lowers
                char_3_legal = ply[2] in lowers
                char_4_legal = ply[3] in nums

                if char_1_legal and char_2_legal and char_3_legal and char_4_legal:
                    return True
                return False

            def pawn_takes():
                char_1_legal = ply[0] in lowers
                char_2_legal = ply[1] == 'x'
                char_3_legal = ply[2] in lowers
                char_4_legal = ply[3] in nums

                if char_1_legal and char_3_legal:
                    pawn_moved_one_rank = abs(lowers.index(ply[0]) - lowers.index(ply[2])) == 1
                else:
                    pawn_moved_one_rank = False

                if char_2_legal and char_4_legal and pawn_moved_one_rank:
                    return True
                return False

            if piece_takes() or pawn_takes():
                return True
            return False

        def is_legal_5_chars():
            def denoted_piece_takes():
                char_1_legal = ply[0] in caps or ply[0] in lowers
                char_2_legal = ply[1] in nums or ply[1] in lowers
                char_3_legal = ply[2] == 'x'
                char_4_legal = ply[3] in lowers
                char_5_legal = ply[4] in nums

                if char_1_legal and char_2_legal and char_3_legal and char_4_legal and char_5_legal:
                    return True
                return False

            longside_castle = ply == 'O-O-O'

            if denoted_piece_takes() or longside_castle:
                return True
            return False

        if len(ply) == 2:
            legal = is_legal_2_chars()
        elif len(ply) == 3:
            legal = is_legal_3_chars()
        elif len(ply) == 4:
            legal = is_legal_4_chars()
        else:
            legal = is_legal_5_chars()
        return legal

    def is_promotion(self):
        ply = self.value

        char_1_is_pawn = ply[0] in Ply.lowercase_letters
        last_char_is_back_rank = ply[len(ply) - 1] == '1' or ply[len(ply) - 1] == '8'

        if char_1_is_pawn and last_char_is_back_rank:
            return True
        return False


def post_process(full_game_encodings):
    possible_pgns, guess_and_index, game_result = read_encodings(full_game_encodings)
    possible_pgns = add_checks_and_mates(possible_pgns)
    result = get_result_from_pgn(possible_pgns, guess_and_index, game_result)
    return result


def read_encodings(full_game_encodings):
    possible_plies = get_plies_worth_checking(full_game_encodings)
    plies = reformat_plies(possible_plies)
    plies = filter_plies(plies)

    fen_num = len(plies) + 1  # There is one board (FEN) to represent state before and after each ply.
    pgns = [[] for i in range(fen_num)]
    boards = [[] for i in range(fen_num)]

    starting_position = chess.pgn.read_game(io.StringIO('e4')).board()
    boards[0] = [starting_position]

    best_guess = []
    game_result = ''
    possible_pgns = []

    def check_move(ply_num, best_guess, game_result):
        for version in plies[ply_num]:
            for board_num in range(len(boards[ply_num])):
                board = boards[ply_num][board_num].copy()
                try:
                    board.push_san(version)

                    # If ValueError does not occur:
                    boards[ply_num + 1].append(board)
                    if ply_num > 0:  # pgns[0][0] is empty.
                        game = pgns[ply_num][board_num] + [version]
                    else:
                        game = [version]
                    pgns[ply_num + 1].append(game)

                    # '*' signifies that multiple full games were found with different results.
                    if game_result != '*' and ply_num == len(plies) - 1:
                        possible_pgns.append(game)
                        if game_result == '':
                            game_result = get_game_result(board, ply_num + 1)
                        elif not game_result == get_game_result(board, ply_num + 1):
                            game_result = '*'

                except ValueError:
                    highest_consecutive_legal_plies = len(best_guess)
                    if ply_num > highest_consecutive_legal_plies:
                        best_guess = pgns.copy()
                    continue

        pgns[ply_num] = []
        boards[ply_num] = []
        return best_guess, game_result

    for ply_num in range(len(plies)):
        best_guess, game_result = check_move(ply_num, best_guess, game_result)

    guess_and_index = get_guess_and_index(best_guess, plies, game_result)
    return possible_pgns, guess_and_index, game_result


def get_game_result(board, move_num):
    if board.is_game_over():
        if board.is_checkmate():
            if move_num % 2 == 0:
                return '0-1'
            else:
                return '1-0'
        else:
            return '1/2-1/2'
    elif board.can_claim_draw():
        return '1/2-1/2'
    else:
        return '*'


def filter_plies(plies):
    for ply_index in range(len(plies)):
        filtered_versions = filter_ply(plies[ply_index])
        plies[ply_index] = filtered_versions
    return plies


def filter_ply(ply_versions):
    for version_index in range(len(ply_versions)):
        version = ply_versions[version_index]
        ply = Ply(value=version)
        if not ply.is_legal_format():
            ply_versions[version_index] = 'TO_BE_REMOVED'
        elif ply.is_promotion():
            ply_versions = add_promotions(ply_versions, version_index)
    ply_versions = list(filter(lambda ply_value: ply_value != 'TO_BE_REMOVED', ply_versions))
    return ply_versions


def add_promotions(ply_versions, version_index):
    ply_template = ply_versions[version_index]

    queen_promotion = ply_template + '=Q'
    rook_promotion = ply_template + '=R'
    knight_promotion = ply_template + '=N'
    bishop_promotion = ply_template + '=B'

    ply_versions[version_index] = queen_promotion
    ply_versions.append(rook_promotion)
    ply_versions.append(knight_promotion)
    ply_versions.append(bishop_promotion)

    return ply_versions


def get_plies_worth_checking(full_game_encodings):
    all_plies = []
    for ply_encoding in full_game_encodings:
        plies = get_versions_worth_checking(ply_encoding)
        all_plies.append(plies)
    return all_plies


def get_versions_worth_checking(ply_encoding):
    chars = get_chars_worth_checking(ply_encoding)
    plies_worth_checking = chars_to_plies(chars)
    return plies_worth_checking


def get_chars_worth_checking(ply_encoding):
    all_chars = []
    for char_encoding in ply_encoding:
        possible_chars = get_versions_of_char(char_encoding)
        all_chars.append(possible_chars)
    return all_chars


def get_versions_of_char(char_encoding):
    if max(char_encoding) > tier_1_confidence:
        possible_versions = get_most_probable_char(char_encoding)
    else:
        possible_versions = get_probable_chars(char_encoding)
    return possible_versions


def get_most_probable_char(char_encoding):
    index_of_most_probable = char_encoding.index(max(char_encoding))
    most_probable_char = one_hot_encoded_mappings[index_of_most_probable]
    return [most_probable_char]


def get_probable_chars(char_encoding):
    possible_chars = get_possible_chars_unsorted(char_encoding)
    # Chars are sorted so that the most probable legal ply will be displayed to the user.
    possible_chars = sort_by_confidence(possible_chars, char_encoding)
    return possible_chars


def get_possible_chars_unsorted(char_encoding):
    min_conf = get_minimum_confidence(char_encoding)
    possible_chars = get_chars_above_conf(char_encoding, min_conf)
    return possible_chars


def get_minimum_confidence(char_encoding):
    if max(char_encoding) > tier_2_confidence:
        min_conf = tier_2_minimum_confidence
    else:
        min_conf = tier_3_minimum_confidence
    return min_conf


def get_chars_above_conf(char_encoding, min_conf):
    possible_chars = []
    for encoding_index in range(len(char_encoding)):
        if char_encoding[encoding_index] > min_conf:
            char_to_check = one_hot_encoded_mappings[encoding_index]
            possible_chars.append(char_to_check)
    return possible_chars


def sort_by_confidence(possible_chars, char_encoding):
    possible_chars.sort(key=lambda char: -char_encoding[one_hot_encoded_mappings.index(char)])
    return possible_chars


def chars_to_plies(chars):
    plies = itertools.product(*chars)
    return plies


def reformat_plies(possible_plies):
    reformatted_plies = []
    for ply in possible_plies:
        reformatted_ply = reformat_ply(ply)
        reformatted_plies.append(reformatted_ply)
    return reformatted_plies


def reformat_ply(ply):
    reformatted_ply = []
    for ply_version in ply:
        reformatted_version = reformat_version(ply_version)
        reformatted_ply.append(reformatted_version)
    return reformatted_ply


def reformat_version(ply_version):
    reformatted_version = ''
    for char in ply_version:
        reformatted_version += char
    return reformatted_version


def add_checks_and_mates(pgns):
    augmented_pgns = []
    for pgn in pgns:
        pgn = augment_pgn(pgn)
        augmented_pgns.append(pgn)
    return augmented_pgns


def augment_pgn(pgn):
    starting_position = chess.pgn.read_game(io.StringIO('e4')).board().copy()
    board = starting_position
    for ply_index in range(len(pgn)):
        board.push_san(pgn[ply_index])
        if board.is_checkmate():
            pgn[ply_index] += '#'
        else:
            if board.is_check():
                pgn[ply_index] += '+'
    return pgn


def get_guess_and_index(best_guess, plies, game_result):
    if game_result == '':
        guess_and_index = get_full_guess(best_guess, plies)
    else:
        guess_and_index = ([], -1)
    return guess_and_index


def reformat_guess(best_guess):
    condensed_guess = list(filter(lambda ply: ply != [], best_guess))
    guess = condensed_guess[len(condensed_guess) - 1][0]  # Element at index 0 is the most likely to be correct.
    return guess


def get_full_guess(best_guess, plies):
    guess = reformat_guess(best_guess)
    checked_len = len(guess)

    for ply_num in range(checked_len, len(plies)):
        if len(plies[ply_num]) > 0:
            guess.append(plies[ply_num][0])
        else:
            guess.append('FIX_THIS_PLY')
    guess_and_index = (guess, checked_len)
    return guess_and_index


def get_result_from_pgn(possible_pgns, guess_and_index, result):
    if len(possible_pgns) == 1:
        pgn, message = process_single_pgn(possible_pgns, result)
    elif len(possible_pgns) == 0:
        pgn, message, result = process_guess(guess_and_index)
    else:
        pgn, message = process_multiple_pgns(possible_pgns, result)

    return message, result, pgn


def process_single_pgn(possible_pgns, result):
    pgn = possible_pgns[0]

    pgn = to_pgn_string(pgn)
    if result != '*' and len(result) > 0:
        pgn += ' ' + result
    message = 'Success! Double check our work if you like.'
    return pgn, message


def to_pgn_string(pgn):
    reformatted = ''
    new_move = True
    move_num = 1
    for ply in pgn:
        if new_move:
            reformatted += str(move_num) + '.' + ply + ' '
            new_move = False
        else:
            reformatted += ply + ' '
            new_move = True
            move_num += 1

    return reformatted.rstrip()


def process_guess(guess_and_index):
    guess = guess_and_index[0]
    index = guess_and_index[1]

    if len(guess) > 0:
        pgn = to_pgn_string(guess)
        up_to = index // 2
        result = 'Game legal up to and including move ' + str(up_to)
        message = 'Sorry—we could only validate the PGN up to move ' + str(up_to) + \
                  '!\nPlease correct the .txt file first, and change the extension to .pgn by renaming the file ' \
                  'when it is corrected.'
    else:
        pgn = ''
        result = ''
        message = 'Sorry, we could\'nt identify any moves!'
    return pgn, message, result


def process_multiple_pgns(possible_pgns, result):
    pgn = possible_pgns[0]

    pgn = to_pgn_string(pgn)
    if result != '*' and result != '':
        pgn += ' ' + result
    message = 'We found multiple possible PGNs—we think this one\'s right:'
    return pgn, message
