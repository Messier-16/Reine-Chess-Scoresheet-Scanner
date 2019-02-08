import chess.pgn
import itertools
import io


# create the_possible_chars
def read_input(probabilities):
    def get_top_3(chars):
        top_3_indices = [0, 1, 2]

        for char in chars:
            if char > chars[top_3_indices[0]]:
                top_3_indices[0] = chars.index(char)
            elif char > chars[top_3_indices[1]]:
                top_3_indices[1] = chars.index(char)
            elif char > chars[top_3_indices[2]]:
                top_3_indices[2] = chars.index(char)

        return top_3_indices

    certain_conf = 1  # chars will be double-checked if they have confidence below this
    min_conf = 0.00001  # chars will not be considered if their confidence is below this

    key = '012345678BKNQRxabcdefgh-'

    all_the_possible_chars = []  # all possible variations of each move
    for move in probabilities:
        this_move = []
        castle_possible = False

        for char in move:
            if max(char) >= certain_conf:
                this_move.append([key[char.index(max(char))]])
            else:
                this_char = []

                top_3 = get_top_3(char)
                for top in top_3:
                    this_char.append(key[top])

                for possible_char in range(len(char)):
                    if char[possible_char] > min_conf and not possible_char in top_3:
                        this_char.append(key[possible_char])
                    possible_char += 1

                if char[0] > 0.1: castle_possible = True


                this_move.append(this_char)

        if castle_possible:
            if len(move) == 3:
                move[1].append('-')
            elif len(move) == 5:
                move[1].append('-')
                move[3].append('-')

        all_the_possible_chars.append(itertools.product(*this_move))

    return all_the_possible_chars


# since the smallest unit we can check for validity is the move, we first find the possible variations of each move
def chars_to_moves(all_possible_chars):
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


def get_pgns(probabilities):
    possible_pgns = []
    possible_moves = chars_to_moves(read_input(probabilities))
    pgn = []
    boards = []
    for move in range(len(possible_moves)):
        pgn.append('')
        boards.append('')  # filling up the list so we can set the value of list elements instead of appending
    boards.append('')  # we use the board of move_num + 1 to calculate validity, thus one extra element is needed
    boards[0] = chess.pgn.read_game(io.StringIO('e4')).board()  # just getting an empty starting board

    globals()['best_guess'] = []  # so we can return the longest correct pgn found instead of nothing
    globals()['highest_checked'] = 0  # to find out which 'guess' is the longest, faster than comparing string length
    globals()['game_result'] = ''  # so we can auto-fill who won/draw if possible

    # if the game result is clear, provides added convenience for user
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

    def check_variations(move_num):
        global best_guess
        global game_result
        global highest_checked

        for possible_move in possible_moves[move_num]:
            # for promotions
            if len(possible_move) == 2 and possible_move[1] == '8' or len(possible_move) == 5 and possible_move[4] == '8':
                possible_move += '=Q'

            boards[move_num + 1] = boards[move_num].copy()

            try:
                boards[move_num + 1].push_san(possible_move)

                # if there is no error
                if move_num == len(possible_moves) - 1:
                    pgn[move_num] = possible_move
                    possible_pgns.append(pgn.copy())
                    if game_result != '*':  # we return '*' if not all games have same result
                        if game_result == '':
                            game_result = get_game_result(boards[move_num + 1], move_num + 1)
                        elif not game_result == get_game_result(boards[move_num + 1], move_num + 1):
                            game_result = '*'
                else:
                    pgn[move_num] = possible_move
                    # if there is no error, we recursively check until we either reach an error or find a completely
                    #   valid game
                    check_variations(move_num + 1)

            except ValueError:
                if move_num > highest_checked:
                    best_guess = pgn.copy()
                    highest_checked = move_num
                continue
        return

    check_variations(0)

    return possible_pgns, best_guess, game_result


# removing pgns including moves that have moves which are notated as, but are not, checks
def check_for_checks(possible_pgn_list):
    checked_pgns = []
    for possible_pgn in range(len(possible_pgn_list)):
        board = chess.pgn.read_game(io.StringIO('e4')).board().copy()  # playing the game out again
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
def list_to_pgn(checked_pgn):
    reformatted = ''
    new_move = True
    move_num = 1
    for half_move in checked_pgn:
        if len(half_move) == 0:
            break
        if new_move:
            reformatted += str(move_num) + '.' + half_move + ' '
            new_move = False
        else:
            reformatted += half_move + ' '
            new_move = True
            move_num += 1

    return reformatted.rstrip()  # remove spaces at end of string


# different result depending on how many error-free PGNs are found
def get_result(checked_pgns, good_guess, result):
    if len(checked_pgns) == 1:
        pgn = list_to_pgn(checked_pgns[0])
        if result != '*' and len(result) > 0:
            pgn += ' ' + result
        message = 'Success! Double check our work if you like.'

    elif not len(checked_pgns) > 0:
        if len(good_guess) > 0:
            pgn = list_to_pgn(good_guess)
            result = 'incomplete'
            message = 'Sorry, we couldn\'t find the full PGN—here\'s as far as we got:'
        else:
            pgn = ''
            result = ''
            message = 'Sorry, we could\'nt even identify the first move!'

    else:
        pgn = list_to_pgn(checked_pgns[0])
        if result != '*' and len(result) > 0:
            pgn += ' ' + result
        message = 'We found multiple possible PGNs—the moves you should double-check are: '

        for half_move in range(len(checked_pgns[0])):
            correct = True
            for possible_pgn in range(len(checked_pgns) - 1):
                if checked_pgns[len(checked_pgns) - 1][half_move] != checked_pgns[possible_pgn][half_move]:
                    correct = False
            if not correct:
                if half_move % 2 == 0:
                    message += 'move ' + str(int(half_move / 2 + 1)) + ' for white, '
                else:
                    message += 'move ' + str(int((half_move + 1) / 2)) + ' for black, '
        message = message[: len(message) - 2] + '.'

    return message, result, pgn  # message tells user how well the program worked, result = winner of game/draw etc.


def post_process(probabilities):
    the_possible_pgns, a_good_guess, game_res = get_pgns(probabilities)
    return get_result(check_for_checks(the_possible_pgns), a_good_guess, game_res)
