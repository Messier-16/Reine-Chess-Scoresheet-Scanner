import numpy as np
from keras.models import model_from_json


def process(imgs):
    # number
    json_file = open('/home/alexfung018/Reine/models/Numbermodel-architecture.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    number = model_from_json(loaded_model_json)
    number.load_weights('/home/alexfung018/Reine/models/Numbermodel_weights.h5')

    # pawn
    json_file = open('/home/alexfung018/Reine/models/Pawnmodel-architecture.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    pawn = model_from_json(loaded_model_json)
    pawn.load_weights('/home/alexfung018/Reine/models/Pawnmodel_weights.h5')

    # piece_letter
    json_file = open('/home/alexfung018/Reine/models/Piece+Lettermodel-architecture.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    piece_letter = model_from_json(loaded_model_json)
    piece_letter.load_weights('/home/alexfung018/Reine/models/Piece+Lettermodel_weights.h5')

    # piece
    json_file = open('/home/alexfung018/Reine/models/Piecemodel-architecture.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    piece = model_from_json(loaded_model_json)
    piece.load_weights('/home/alexfung018/Reine/models/Piecemodel_weights.h5')

    # letter_x_number
    json_file = open('/home/alexfung018/Reine/models/Letter+x+Numbermodel-architecture.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    letter_x_number = model_from_json(loaded_model_json)
    letter_x_number.load_weights('/home/alexfung018/Reine/models/Letter+x+Numbermodel_weights.h5')

    def identify_chars(move):
        prediction = []

        def number_model(char):
            possibilities = number.predict(char)[0]
            return np.append(possibilities, np.zeros(15))

        def pawn_model(char):
            possibilities = np.zeros(15)
            possibilities = np.append(possibilities, pawn.predict(char)[0])
            return np.append(possibilities, 0.0)

        def piece_letter_model(char):
            possibilities = np.zeros(9)
            possibilities = np.append(possibilities, piece_letter.predict(char)[0])
            possibilities = np.insert(possibilities, 14, 0.0)
            return np.append(possibilities, 0.0)

        def piece_model(char):
            possibilities = np.zeros(9)
            possibilities = np.append(possibilities, piece.predict(char)[0])
            return np.append(possibilities, np.zeros(10))

        def letter_x_number_model(char):
            possibilities = letter_x_number.predict(char)[0]
            possibilities = np.insert(possibilities, 9, np.zeros(5))
            return np.append(possibilities, 0.0)

        if len(move) == 2:
            first = pawn_model(move[0])
            second = number_model(move[1])

            prediction.append(first.tolist())
            prediction.append(second.tolist())

        elif len(move) == 3:
            third = number_model(move[2])
            castle = False

            if third[0] > 0.5:
                first = letter_x_number_model(move[0])
                if first[0] > 0.5:
                    # assume that the move is '0-0'
                    first[0] = 1.0
                    second = np.zeros(23)
                    second = np.append(second, 1.0)
                    third[0] = 1.0
                    castle = True
            if not castle:
                first = piece_model(move[0])
                second = pawn_model(move[1])

            prediction.append(first.tolist())
            prediction.append(second.tolist())
            prediction.append(third.tolist())

        elif len(move) == 4:
            first = piece_letter_model(move[0])
            second = letter_x_number_model(move[1])
            third = pawn_model(move[2])
            fourth = number_model(move[3])

            prediction.append(first.tolist())
            prediction.append(second.tolist())
            prediction.append(third.tolist())
            prediction.append(fourth.tolist())

        elif len(move) == 5:
            fifth = number_model(move[4])
            castle = False

            if fifth[0] > 0.5:
                third = letter_x_number_model(move[2])
                if third[0] > 0.5:
                    first = letter_x_number_model(move[0])
                    if first[0] > 0.5:
                        # assume the move is '0-0-0'
                        first[0] = 1.0
                        second = np.zeros(23)
                        second = np.append(second, 1.0)
                        third[0] = 1.0
                        fourth = np.zeros(23)
                        fourth = np.append(fourth, 1.0)
                        fifth[0] = 1.0
                        castle = True
            if not castle:
                first = piece_letter_model(move[0])
                second = letter_x_number_model(move[1])
                # assume that char 3 must be an 'x'
                third = np.zeros(14)
                third = np.append(third, 1.0)
                third = np.append(third, np.zeros(9))
                fourth = pawn_model(move[3])

            prediction.append(first.tolist())
            prediction.append(second.tolist())
            prediction.append(third.tolist())
            prediction.append(fourth.tolist())
            prediction.append(fifth.tolist())

        else:
            return 'end'

        return prediction

    def read_game(processed_imgs):

        predictions = []
        pop = 0
        done = False

        while not done:
            move = []
            for i in range(pop, pop + 5):
                # less than 3 means there is no char
                if np.mean(processed_imgs[i]) > 3:
                    char = processed_imgs[i].reshape(-1, 28, 28, 1) / 255.0
                    move.append(char)

            prediction = identify_chars(move)
            if prediction == 'end':
                done = True
            else:
                predictions.append(prediction)

            pop += 5
            if pop == 500:
                done = True

        return predictions

    return read_game(imgs)
