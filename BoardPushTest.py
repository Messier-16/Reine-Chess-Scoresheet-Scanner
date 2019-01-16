import chess.pgn
import io
import time

total_1 = 0
total_2 = 0

for x in range(1000):
    pgn = io.StringIO('1. a4 a5 2. b4 b5 3. c4 c5 4. d4 d5 5. e4 e5 6. f4 f5 7. g4 g5 8. h4 h5')
    time_1 = time.time()
    game = chess.pgn.read_game(pgn)
    time_2 = time.time()
    total_1 += time_2 - time_1

for y in range(1000):
    pgn = io.StringIO('1. a4 a5 2. b4 b5 3. c4 c5 4. d4 d5 5. e4 e5 6. f4 f5 7. g4 g5 8. h4 h5')
    game = chess.pgn.read_game(pgn)
    board = game.board()

    time_3 = time.time()
    for move in game.mainline_moves():
        board.push(move)
    time_4 = time.time()

    total_2 += time_4 - time_3

print('The old method takes:')
print(total_1)

print('The new method takes:')
print(total_2)
