import chess.pgn
import itertools
import io


# create the_possible_chars
def read_input(probabilities):
    # make sure that we get at least 2 possible chars. The algorithm sometimes has .99 confidence in the wrong answer,
    # for example, but the second highest confidence at 0.00001 or something is correct
    def get_top_2(chars):
        top_2_indices = [0, 1]

        for char in chars:
            if char > chars[top_2_indices[0]]:
                top_2_indices[0] = chars.index(char)
            elif char > chars[top_2_indices[1]]:
                top_2_indices[1] = chars.index(char)

        return top_2_indices

    certain_conf = 1.0  # chars will be double-checked if they have confidence below this
    min_conf = 0.001  # chars will not be considered if their confidence is below this

    key = 'O12345678BKNQRxabcdefgh-'  # the mappings for the list of probabilities that is the function param

    all_the_possible_moves = []  # all possible variations of each move
    #  structure: one list for each move, one list of 24 float probabilities
    #  from 0.0 to 1.0 for each char within that move
    for move in probabilities:
        this_move = []
        castle_possible = False
        for char in move:
            if max(char) >= certain_conf:
                the_char = key[char.index(max(char))]
                this_move.append([the_char])
                if the_char == 'O':
                    castle_possible = True
            else:
                this_char = []  # a list of the possibilities for this char

                top_2 = get_top_2(char)
                for top in top_2:
                    this_char.append(key[top])

                for possible_char in range(len(char)):
                    if char[possible_char] > min_conf and possible_char not in top_2:
                        this_char.append(key[possible_char])

                # chars with a higher probability are sorted first so that the higher probability char will be displayed
                this_char.sort(key=lambda selected_char: -char[key.index(selected_char)])

                this_move.append(this_char)
                if char[0] > min_conf:  # the first element in the list corresponds to 'O'
                    castle_possible = True

        # model does not recognize '-' so it must be added manually
        if castle_possible:
            if len(move) == 3:
                this_move[1].append('-')
            elif len(move) == 5:
                this_move[1].append('-')
                this_move[3].append('-')

        # finds all possible moves (list form) from the chars in each position of the move
        all_the_possible_moves.append(itertools.product(*this_move))

    return all_the_possible_moves


# since the smallest unit we use to check for game legality is the move,
# we must reformat the list into moves
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


# the bread and butter. Eliminates impossible moves and then finds valid pgns out of the remaining ones if possible.
def get_pgns(probabilities):
    possible_pgns = []
    possible_moves = chars_to_moves(read_input(probabilities))

    # eliminate 'moves' that cannot be legal
    def legal(h_move):
        nums = ['1', '2', '3', '4', '5', '6', '7', '8']
        pawns = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        caps = ['B', 'K', 'N', 'Q', 'R']

        if len(h_move) == 2:
            if h_move[0] in pawns and h_move[1] in nums:
                return True
        elif len(h_move) == 3:
            if (h_move[0] in caps and h_move[1] in pawns and h_move[2] in nums) or h_move == 'O-O':
                return True
        elif len(h_move) == 4:
            # when the first char is a piece
            if h_move[0] in caps and (h_move[1] == 'x' or h_move[1] in nums or h_move[1] in pawns) and \
                    h_move[2] in pawns and h_move[3] in nums:
                return True
            # when the first char is a pawn
            elif h_move[0] in pawns and h_move[1] == 'x' and h_move[2] in pawns and h_move[3] in nums:
                return True
        else:
            if (h_move[0] in caps or h_move[0] in pawns) and (h_move[1] in nums or h_move[1] in pawns) and \
                    h_move[2] == 'x' and h_move[3] in pawns and h_move[4] in nums:
                return True
        return False

    for move in range(len(possible_moves)):
        for char in range(len(possible_moves[move])):
            if not legal(possible_moves[move][char]):
                possible_moves[move][char] = -1
        # remove the illegal moves from the list
        possible_moves[move] = list(filter(lambda a: a != -1, possible_moves[move]))

    pgn = []  # global list that is updated once for each move
    boards = []  # second global variable
    for move in range(len(possible_moves)):
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

        for _move in possible_moves[move_num]:
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
                    if game_result != '*' and move_num == len(possible_moves) - 1:
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

    for x in range(len(possible_moves)):  # carry out once for each move
        check_iterative(x)

    # best_guess has empty lists at the end because the check_iterative() function did not find the full game
    no_space = list(filter(lambda a: a != [], best_guess))
    guess = no_space[len(no_space) - 1][0]  # guess will be the first element in the last non-empty list

    guess_len = len(guess)  # for telling the user how many moves were validated

    # use the most likely char with no game validity checking for the rest of the moves
    for half_move in range(guess_len, len(possible_moves)):
        if len(possible_moves[half_move]) > 0:
            guess.append(possible_moves[half_move][0])
        else:  # when there is not a single move that could be found based on the probabilities of the chars
            guess.append('FIX_THIS')
    guess_and_index = [guess, guess_len]

    return possible_pgns, guess_and_index, game_result


# while users cannot currently input checks (lacking model/database), we can still add them afterward with python chess
def check_for_checks(possible_pgn_list):
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
# remember that result == '*' when game is inconclusive, else it will be '1-0', '1/2-1/2', or '0-1'
def get_result(checked_pgns, good_guess, result):
    if len(checked_pgns) == 1:
        pgn = list_to_pgn(checked_pgns[0])
        if result != '*' and len(result) > 0:
            pgn += ' ' + result
        message = 'Success! Double check our work if you like.'

    elif not len(checked_pgns) > 0:
        if len(good_guess[0]) > 0:
            pgn = list_to_pgn(good_guess[0])
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
        pgn = list_to_pgn(checked_pgns[0])
        if result != '*' and len(result) > 0:
            pgn += ' ' + result
        message = 'We found multiple possible PGNs—but we think this one\'s right:'

    return message, result, pgn  # message tells user how well the program worked, result = winner of game/draw etc.


def post_process(probabilities):
    the_possible_pgns, a_good_guess, game_res = get_pgns(probabilities)
    return get_result(check_for_checks(the_possible_pgns), a_good_guess, game_res)


# test_probabilities = [[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.587351692426523e-10, 2.649655885325619e-12, 1.6629907520493425e-11, 7.507844714850498e-13, 1.0, 3.872794554667103e-13, 6.25026430611797e-09, 7.590749449726579e-18, 0.0], [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.1852330460123617e-33, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.6638684264289623e-07, 3.173059681671475e-08, 1.0275376780555234e-06, 5.6379536594874935e-09, 0.9999953508377075, 6.067868874026772e-09, 3.2410043786512688e-06, 1.2843307146959138e-11, 0.0], [3.3208834105193413e-28, 0.0, 1.8467368606319993e-27, 4.434820004019912e-22, 1.56356343352273e-24, 1.0, 4.029872886961332e-21, 2.0739621520381943e-32, 1.246124514472046e-17, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.6090676022277227e-21, 1.234298157330022e-23, 1.5032141630011632e-20, 1.1697378400113024e-24, 1.897483834641926e-17, 1.0, 3.2035666979422783e-15, 6.886424907074801e-19, 0.0], [0.0, 5.0575304652793135e-34, 1.5210586569131783e-31, 0.0, 1.0, 1.06550708455992e-36, 0.0, 2.806745956779745e-20, 6.347820209883734e-20, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.014311347156763077, 6.666713829872606e-07, 1.380972142195347e-10, 0.0003485711058601737, 0.0022042414639145136, 0.0, 8.670632087159902e-05, 2.3618036721018143e-05, 0.0001746302004903555, 9.940273457686999e-07, 0.9738405346870422, 0.00013528626004699618, 0.008873363956809044, 2.289495171226008e-08, 0.0], [1.540684317625354e-23, 2.955512709736788e-19, 1.302996395224909e-07, 9.718542295792179e-14, 3.662633503154211e-07, 7.877907217695057e-16, 3.4348498912230123e-15, 6.817299275010263e-14, 1.050407405500664e-07, 0.0, 0.0, 0.0, 0.0, 0.0, 0.9999986886978149, 2.1837493632500572e-14, 1.2807836735628797e-10, 6.02720522580816e-36, 7.020455683459659e-08, 4.277797883536426e-19, 2.6448667305486572e-15, 3.982586829764934e-12, 6.017115765644121e-07, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.6613056416647787e-13, 9.991570288150897e-13, 2.323453891402031e-17, 5.635001471514245e-13, 2.5046802739486784e-12, 1.0, 3.3980800395738697e-09, 2.4102739248910154e-10, 0.0], [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2.4432943190356993e-14, 1.2359762464799612e-14, 1.3868846071574126e-09, 4.5680486060462044e-09, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0001447945978725329, 7.4973409027734306e-06, 0.9901206493377686, 1.497365337854717e-05, 0.009578597731888294, 5.03972805745434e-05, 8.027452713577077e-05, 2.7815608518722e-06, 0.0], [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 2.480092452501601e-28, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.7352976965524097e-13, 2.696166553906032e-11, 3.938497084021719e-09, 5.451631679420643e-08, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.373188090487588e-09, 1.3707006992109971e-13, 1.0, 1.1623703735641477e-11, 5.8997233765012425e-09, 4.733592406935827e-10, 3.004507198589579e-10, 4.751658593503405e-13, 0.0], [0.0, 0.0, 1.1960953440137738e-37, 2.4421703519391123e-38, 7.447561850481708e-27, 1.0, 0.0, 8.017348676392236e-38, 1.395443788636647e-25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 6.923701612038258e-10, 1.5854768127716856e-13, 4.809378861101283e-23, 1.0, 2.493529504532324e-17, 6.779305617455128e-17, 1.0389410685929246e-12, 1.2056828966268873e-15, 0.0], [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 7.311024745968698e-38, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.999996542930603, 4.077301864191529e-12, 4.849481372026787e-10, 3.440982482061372e-06, 4.119734597907154e-08, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.7064251284514285e-08, 0.999992847442627, 4.5166639872640246e-10, 1.2800485365005443e-06, 1.9326348521531145e-08, 1.1574083025323034e-08, 3.3045755571947666e-06, 2.5709714464028366e-06, 0.0], [2.3763510224802062e-23, 0.0, 1.4126614290057739e-28, 0.0, 1.483396021038256e-28, 3.007081810882033e-25, 1.0, 0.0, 3.750008085149124e-23, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.4292453537980776e-18, 3.375444726245319e-13, 1.0, 7.474851900640678e-13, 2.877342678356265e-12, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.4584133714237328e-17, 1.7777007365804082e-16, 4.607575225340812e-24, 1.3617423114718286e-16, 1.0032812438290344e-17, 1.0, 8.86720297882393e-12, 4.5597260776159e-13, 0.0], [3.6661256701280955e-26, 2.1728304839603614e-32, 5.3167461544489925e-09, 1.0, 5.740676491369001e-24, 9.62461013664928e-13, 3.424419767289146e-27, 4.423009538918193e-15, 1.9110232195524227e-14, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.690019044917717e-20, 9.17883102830681e-15, 1.0, 3.974748522396314e-14, 3.598158690486589e-15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.042755378951175e-16, 1.4154148850468423e-17, 7.265503687231954e-18, 1.428503694751514e-17, 1.2002123343370454e-16, 1.0, 8.599536013842446e-12, 1.2882448920616585e-15, 0.0], [2.0871438518147277e-33, 0.0, 2.4679188210995883e-35, 0.0, 0.0, 3.237349057983806e-31, 1.0, 0.0, 1.8756582827822296e-30, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[1.0, 4.1858831423269294e-07, 0.00010166348511120304, 2.9252429158077575e-05, 5.129906185175059e-06, 4.821355832973495e-05, 0.00022111964062787592, 9.653854249336291e-06, 0.000867629365529865, 0.0, 0.0, 0.0, 0.0, 0.0, 1.8340712131248438e-06, 0.0007914378657005727, 5.676959699485451e-05, 1.3178301742300391e-05, 0.00011779783380916342, 0.00011226292554056272, 6.187561893966631e-07, 0.00036238363827578723, 8.76902674917801e-08, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], [1.0, 2.1689288712731884e-33, 2.147564606532638e-25, 4.0995718477615634e-35, 4.802656835579451e-28, 1.2896948024990236e-31, 6.458189285225568e-30, 3.01698466532216e-26, 4.456504371556401e-17, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[1.0, 1.4200621478721587e-07, 0.00010694946104194969, 1.7990463675232604e-05, 6.739517630194314e-06, 2.338267586310394e-05, 8.912709745345637e-05, 1.4406693480850663e-05, 0.0006316183716990054, 0.0, 0.0, 0.0, 0.0, 0.0, 2.5235715384042123e-06, 0.0017416373593732715, 2.0559122276608832e-05, 8.890497156244237e-06, 0.00011889116285601631, 7.23354023648426e-05, 1.685834831732791e-07, 0.0003589885600376874, 6.285461751076582e-08, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], [1.0, 1.1189114021913538e-34, 2.9633512800164936e-19, 4.554876318584311e-28, 7.104273842002359e-24, 1.352247028876788e-26, 3.501362305607869e-28, 1.141560034212789e-17, 1.721055408232777e-16, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 6.874065691349916e-18, 3.5819454634366046e-14, 1.0, 5.5785393665575e-12, 4.3918422501162957e-13, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.2403863491883271e-09, 2.115062031765591e-12, 1.0, 4.129820790899075e-11, 3.302080386902162e-09, 3.4572253948539355e-09, 9.780106724477378e-10, 1.5060067993025172e-12, 0.0], [1.1935987861855776e-35, 0.0, 1.353334355387939e-13, 1.0, 6.635740162538107e-25, 2.2429581335804133e-17, 0.0, 4.982845386303225e-11, 3.912871594973384e-18, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.028419810815124e-17, 7.081526798334917e-14, 1.0, 1.9214306794940184e-12, 8.240105239852927e-14, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.6897091503764727e-09, 4.664092462941527e-13, 1.0, 6.929243637210369e-12, 1.316717623822683e-09, 1.3211080229780237e-08, 4.2910226483172664e-09, 1.1578425935035441e-12, 0.0], [6.2686446869265955e-22, 0.0, 2.2657926326788982e-30, 0.0, 1.044414241078125e-32, 1.121137669629055e-26, 1.0, 0.0, 3.0472250313331873e-22, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.9999998807907104, 6.510410700127922e-13, 8.787344983607337e-12, 7.693885351045537e-08, 1.2714951314052314e-09, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.145419202876809e-10, 8.723055264225898e-12, 2.48362190609397e-22, 5.86290618918156e-13, 8.306781911632255e-13, 2.8314321373623663e-12, 1.0, 1.3287022561169577e-15, 0.0], [4.2894515521994803e-13, 0.0, 8.151432262280792e-24, 0.0, 0.00010837830632226542, 0.00010502141230972484, 0.0, 8.530072806954558e-13, 0.9997865557670593, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9.17765104364865e-13, 5.838736807069005e-16, 7.479004071226781e-24, 1.0, 2.6735547769426498e-17, 5.908965536923633e-14, 5.201097256872511e-13, 3.6510852265584184e-16, 0.0], [1.2314247968184232e-38, 0.0, 5.300067092277607e-33, 1.070275076985513e-25, 2.5481990378933285e-30, 1.0, 3.974283764858354e-23, 0.0, 1.5008502734566306e-24, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.6668989322524141e-12, 1.6646172953494326e-20, 1.3632737300151021e-11, 1.0, 1.2338645562847648e-16, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.535449876248322e-10, 2.8504762439318654e-10, 4.710206753475723e-16, 1.0, 1.2987072355030715e-12, 1.8713677829573783e-10, 2.006655730468765e-09, 3.971480838692396e-15, 0.0], [2.7775737522674434e-19, 2.273815844474161e-33, 1.0, 5.3309590628599496e-14, 1.005261431497425e-18, 4.0417615887089086e-27, 1.4993447817228229e-25, 3.7155096843178095e-14, 4.57965306302488e-12, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.760512315575397e-10, 2.1265000368835625e-17, 3.6241307264234246e-12, 1.0, 9.451933159765336e-12, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.850079792755423e-06, 1.3487540077850024e-11, 2.2786248691239927e-19, 0.9999961853027344, 7.969363016724351e-13, 1.6768674122868976e-12, 1.1711559722016318e-08, 9.83765477934051e-14, 0.0], [0.0, 0.0, 9.344549364990084e-18, 3.604978155950258e-20, 4.699749030945419e-21, 4.295818330156616e-37, 0.0, 1.0, 7.276353593284555e-24, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.3716217878444468e-09, 1.744237306411378e-05, 8.237569900835205e-15, 7.729280548929296e-10, 0.9999825954437256, 0.0, 4.780955159219315e-14, 7.873960705905342e-17, 5.09936797555744e-25, 1.0008554539646614e-17, 3.0248511486384577e-13, 6.651675044100358e-11, 8.316052924409179e-13, 1.6907280697003868e-12, 0.0], [8.740671546547674e-07, 2.7232049961919448e-14, 0.0007501171203330159, 1.1703997770950991e-08, 0.00016620178939774632, 1.07482611699794e-09, 1.2171345709077741e-08, 1.923291392813553e-08, 0.00017815212777350098, 0.0, 0.0, 0.0, 0.0, 0.0, 2.6027681087725796e-05, 0.9904734492301941, 1.0155772889319792e-09, 6.461505809574053e-12, 0.00038553698686882854, 1.1161123438796494e-06, 8.824156683129303e-11, 0.008018153719604015, 2.297633585612857e-07, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.003477410696732e-11, 6.959568284083811e-14, 1.0, 1.3721270213790104e-12, 2.1551815887477233e-09, 9.294375165336266e-13, 2.8997125881002894e-11, 9.556347471909184e-16, 0.0], [0.0, 1.0, 3.822470919295408e-37, 0.0, 3.66766351835666e-19, 6.713231448869443e-36, 2.0671241191978367e-30, 3.6319084801406835e-35, 1.157073056599139e-29, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]]
# print(post_process(test_probabilities))
