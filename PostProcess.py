import chess.pgn
import itertools
import io

tier_1_confidence = 0.99
tier_2_confidence = 0.95
tier_2_minimum_confidence = 0.025
tier_3_minimum_confidence = 0.01
mappings_by_list_index = 'O12345678BKNQRxabcdefgh-'


def post_process(full_game_encodings):
    # Model predictions are one hot encoded.
    the_possible_pgns, a_good_guess, game_res = read_encodings(full_game_encodings)
    result = get_result_from_pgn(remove_moves_with_illegal_checks(the_possible_pgns), a_good_guess, game_res)
    return result


def read_encodings(full_game_encodings):
    possible_pgns = []
    possible_plies = get_plies_worth_checking(full_game_encodings)
    plies = list_to_string(possible_plies)

    for move in range(len(plies)):
        for char in range(len(plies[move])):
            ply = plies[move][char]
            if not is_legal_format(ply):
                plies[move][char] = -1
            elif is_promotion(ply):
                plies[move][char] += '=Q'
        # remove the illegal moves from the list
        plies[move] = list(filter(lambda a: a != -1, plies[move]))

    pgn = []  # global list that is updated once for each move
    boards = []  # second global variable
    for move in range(len(plies) + 1):
        pgn.append([])
        boards.append([])  # filling up the list so we can set the value of list elements instead of appending
    boards.append([])  # we use the board of move_num + 1 to calculate validity, thus one extra element is needed
    boards[0] = [chess.pgn.read_game(io.StringIO('e4')).board()]  # just getting an empty starting board

    globals()['best_guess'] = []  # so we can return the longest correct pgn found instead of nothing
    globals()['highest_checked'] = 0  # to find out which 'guess' is the longest, faster than comparing string length
    globals()['game_result'] = ''  # so we can auto-fill who won/draw if possible

    # if the game result is clear, provides added convenience for user, else it will be '*'.
    # the result field is required for a .pgn file
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

    # out of the possible moves at this move num and all the legal boards thus far, finds all the legal
    # combinations for the next move
    def check_iterative(move_num):
        global best_guess  # so we can check some moves even if we don't find a valid pgn spanning the whole game
        global game_result
        global highest_checked  # the highest move num for which a valid pgn was found

        for _move in plies[move_num]:
            # boards are an object from python chess library representing an FEN
            for board_num in range(len(boards[move_num])):
                new_board = boards[move_num][board_num].copy()
                try:
                    # python chess function that makes this move on the board, if the move is illegal a
                    # ValueError will occur here
                    new_board.push_san(_move)

                    # if there is no error
                    boards[move_num + 1].append(new_board)
                    if len(pgn[move_num]) > 0:
                        game = pgn[move_num][board_num] + [_move]
                    else:  # only occurs on move 1
                        game = [_move]
                    pgn[move_num + 1].append(game)

                    # we return '*' if not all games have same result
                    if game_result != '*' and move_num == len(plies) - 1:
                        possible_pgns.append(game)
                        if game_result == '':
                            game_result = get_game_result(new_board, move_num + 1)
                        elif not game_result == get_game_result(new_board, move_num + 1):
                            game_result = '*'

                except ValueError:
                    if move_num > highest_checked:
                        best_guess = pgn.copy()
                        highest_checked = move_num
                    continue

        pgn[move_num] = []  # clear variables that are no longer necessary to save memory
        boards[move_num] = []

        return  # no return value needed because the modifies globals

    for x in range(len(plies)):  # carry out once for each move
        check_iterative(x)

    # best_guess has empty lists at the end because the check_iterative() function did not find the full game
    if len(best_guess) > 0:
        no_space = list(filter(lambda a: a != [], best_guess))
        guess = no_space[len(no_space) - 1][0]  # guess will be the first element in the last non-empty list
    else:
        guess = []

    guess_len = len(guess)  # for telling the user how many moves were validated

    # use the most likely char with no game validity checking for the rest of the moves
    for ply_num in range(guess_len, len(plies)):
        if len(plies[ply_num]) > 0:
            guess.append(plies[ply_num][0])
        else:  # when there is not a single move that could be found based on the probabilities of the chars
            guess.append('FIX_THIS_PLY')
    guess_and_index = [guess, guess_len]

    return possible_pgns, guess_and_index, game_result


def get_plies_worth_checking(full_game_encodings):
    all_plies = []
    for ply_encoding in full_game_encodings:
        plies = get_versions_worth_checking(ply_encoding)
        all_plies.append(plies)
    return all_plies


def get_versions_worth_checking(ply_encoding):
    chars = get_chars_worth_checking(ply_encoding)
    chars = handle_castles_if_necessary(ply_encoding, chars)
    plies_worth_checking = chars_to_plies(chars)
    return plies_worth_checking


def get_chars_worth_checking(ply_probabilities):
    possible_versions_of_all_chars = []
    for char_probabilities in ply_probabilities:
        possible_versions_of_char = get_versions_of_char_from_probabilities(char_probabilities)
        possible_versions_of_all_chars.append(possible_versions_of_char)
    return possible_versions_of_all_chars


def get_versions_of_char_from_probabilities(char_probabilities):
    if max(char_probabilities) > tier_1_confidence:
        possible_versions_of_char = get_most_probable_char(char_probabilities)
    else:
        possible_versions_of_char = get_tier_2_to_3_chars(char_probabilities)
    return possible_versions_of_char


def get_most_probable_char(char_probabilities):
    most_probable_char = mappings_by_list_index[char_probabilities.index(max(char_probabilities))]
    return [most_probable_char]


def get_tier_2_to_3_chars(char_probabilities):
    possible_versions_of_char = get_possible_versions_of_char_from_probabilities(char_probabilities)
    # Chars are sorted -> highest probability legal char is displayed to user
    possible_versions_of_char = sort_possible_versions_of_char(possible_versions_of_char, char_probabilities)
    return possible_versions_of_char


def get_possible_versions_of_char_from_probabilities(char_probabilities):
    possible_versions_of_char = tier_2_to_3_chars(char_probabilities)
    return possible_versions_of_char


def tier_2_to_3_chars(char_probabilities):
    possible_versions_of_char = []
    if max(char_probabilities) > tier_2_confidence:
        minimum_confidence = tier_2_minimum_confidence
    else:
        minimum_confidence = tier_3_minimum_confidence

    for possible_char in range(len(char_probabilities)):
        if char_probabilities[possible_char] > minimum_confidence and \
                mappings_by_list_index[possible_char] not in possible_versions_of_char:
            possible_versions_of_char.append(mappings_by_list_index[possible_char])
    return possible_versions_of_char


def sort_possible_versions_of_char(possible_versions_of_char, char_probabilities):
    possible_versions_of_char.sort(
        key=lambda selected_char: -char_probabilities[mappings_by_list_index.index(selected_char)])
    return possible_versions_of_char


def handle_castles_if_necessary(ply_probabilities, possible_versions_of_all_chars):
    # Model does not recognize '-' so it must be added manually (castle notation is 'O-O' or 'O-O-O')
    castle_possible = has_capital_o(ply_probabilities)
    if castle_possible:
        possible_versions_of_all_chars = add_dashes(possible_versions_of_all_chars)
    return possible_versions_of_all_chars


def has_capital_o(ply_probabilities):
    o_minimum_confidence = 0.1
    for char_probabilities in ply_probabilities:
        if char_probabilities[0] > o_minimum_confidence:
            return True
    return False


def add_dashes(possible_versions_of_all_chars):
    if len(possible_versions_of_all_chars) == 3:
        if not ('-' in possible_versions_of_all_chars[1]):
            possible_versions_of_all_chars[1].append('-')
    elif len(possible_versions_of_all_chars) == 5:
        if not ('-' in possible_versions_of_all_chars[1]):
            possible_versions_of_all_chars[1].append('-')
            possible_versions_of_all_chars[3].append('-')
    return possible_versions_of_all_chars


def chars_to_plies(possible_versions_of_all_chars):
    possible_versions_of_plies = itertools.product(*possible_versions_of_all_chars)
    return possible_versions_of_plies


# since the smallest unit we use to check for game legality is the move, we must reformat the list into moves
def list_to_string(all_possible_chars):
    the_possible_moves = []

    for move_list in all_possible_chars:
        new_list = []
        for possible_move in move_list:
            new_move = ''
            for char in possible_move:
                new_move += char
            new_list.append(new_move)
        the_possible_moves.append(new_list)

    return the_possible_moves


# eliminate plies that cannot be legal
numbers = ['1', '2', '3', '4', '5', '6', '7', '8']
lowercase_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
capital_letters = ['B', 'K', 'N', 'Q', 'R']


def is_legal_format(ply):
    if len(ply) == 2:
        legal = is_legal_2_chars(ply)
    elif len(ply) == 3:
        legal = is_legal_3_chars(ply)
    elif len(ply) == 4:
        legal = is_legal_4_chars(ply)
    else:
        legal = is_legal_5_chars(ply)
    return legal


def is_legal_2_chars(ply):
    if ply[0] in lowercase_letters and ply[1] in numbers:
        return True
    return False


def is_legal_3_chars(ply):
    if (ply[0] in capital_letters and ply[1] in lowercase_letters and ply[2] in numbers) or ply == 'O-O':
        return True
    return False


def is_legal_4_chars(ply):
    if ply[0] in capital_letters and (ply[1] == 'x' or ply[1] in numbers or ply[1] in lowercase_letters) and \
            ply[2] in lowercase_letters and ply[3] in numbers:
        return True
    elif ply[0] in lowercase_letters and ply[1] == 'x' and ply[2] in lowercase_letters and ply[3] in numbers and \
            abs(lowercase_letters.index(ply[0]) - lowercase_letters.index(ply[2])) == 1:
        return True
    return False


def is_legal_5_chars(ply):
    if ((ply[0] in capital_letters or ply[0] in lowercase_letters) and
            (ply[1] in numbers or ply[1] in lowercase_letters) and ply[2] == 'x' and ply[3] in lowercase_letters
            and ply[4] in numbers) or ply == 'O-O-O':
        return True
    return False


def is_promotion(ply):
    if ply[0] in lowercase_letters and (ply[len(ply) - 1] == '1' or ply[len(ply) - 1] == '8'):
        return True
    return False


# while users cannot currently input checks (lacking model/database), we can still add them afterward with python chess
def remove_moves_with_illegal_checks(possible_pgn_list):
    checked_pgns = []
    for possible_pgn in range(len(possible_pgn_list)):
        board = chess.pgn.read_game(io.StringIO('e4')).board().copy()  # playing the game out again from scratch
        for half_move in range(len(possible_pgn_list[possible_pgn])):
            board.push_san(possible_pgn_list[possible_pgn][half_move])
            if board.is_checkmate():
                possible_pgn_list[possible_pgn][half_move] += '#'
            else:
                if board.is_check():
                    possible_pgn_list[possible_pgn][half_move] += '+'
        checked_pgns.append(possible_pgn_list[possible_pgn])

    return checked_pgns


# checked_pgns format is a list of single-unit lists, we need to reformat it into a pgn
def get_pgn_from_list(checked_pgn):
    reformatted = ''
    new_move = True
    move_num = 1
    for ply in checked_pgn:
        if len(ply) == 0:
            break
        if new_move:
            reformatted += str(move_num) + '.' + ply + ' '
            new_move = False
        else:
            reformatted += ply + ' '
            new_move = True
            move_num += 1

    return reformatted.rstrip()  # remove spaces at end of string


# different result depending on how many error-free PGNs are found
# remember that result == '*' when game is inconclusive, else it will be '1-0', '1/2-1/2', or '0-1'
def get_result_from_pgn(checked_pgns, good_guess, result):
    if len(checked_pgns) == 1:
        pgn = get_pgn_from_list(checked_pgns[0])
        if result != '*' and len(result) > 0:
            pgn += ' ' + result
        message = 'Success! Double check our work if you like.'

    elif not len(checked_pgns) > 0:
        if len(good_guess[0]) > 0:
            pgn = get_pgn_from_list(good_guess[0])
            up_to = good_guess[1] // 2
            result = 'Game legal up to and including move ' + str(up_to)
            message = 'Sorry—we could only validate the PGN up to move ' + str(up_to) + \
                      '!\nPlease correct the .txt file first, and change the extension to .pgn by renaming ' \
                      'the file when it is corrected.'
        else:
            pgn = ''
            result = ''
            message = 'Sorry, we could\'nt even identify the first move!'

    else:
        pgn = get_pgn_from_list(checked_pgns[0])
        if result != '*' and len(result) > 0:
            pgn += ' ' + result
        message = 'We found multiple possible PGNs—but we think this one\'s right:'

    return message, result, pgn  # message tells user how well the program worked, result = winner of game/draw etc.
