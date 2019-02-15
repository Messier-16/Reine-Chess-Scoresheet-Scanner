import numpy as np
from keras.models import model_from_json


def process(imgs):
    # load the model that recognizes digits only
    json_file = open('/Reine/models/Numbermodel-architecture.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    number = model_from_json(loaded_model_json)
    number.load_weights('/Reine/models/Numbermodel_weights.h5')

    # load the model that recognizes lowercase letters only, to indicate the file of a square
    json_file = open('/home/alexfung018/Reine/models/Pawnmodel-architecture.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    pawn = model_from_json(loaded_model_json)
    pawn.load_weights('/Reine/models/Pawnmodel_weights.h5')

    # load the model that recognizes both pieces and lowercase letters, to allow for variation between either one
    # in the first box of any n=4 or n=5 move
    json_file = open('/Reine/models/Piece+Lettermodel-architecture.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    piece_letter = model_from_json(loaded_model_json)
    piece_letter.load_weights('/Reine/models/Piece+Lettermodel_weights.h5')

    # load the model that recognizes pieces only, for n=3 first box
    json_file = open('/Reine/models/Piecemodel-architecture.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    piece = model_from_json(loaded_model_json)
    piece.load_weights('/Reine/models/Piecemodel_weights.h5')

    # load the model that recognizes lowercase letters, "x" for captures, and digits
    # this is only for n=4, to detect whether the second box is a capture, 
    json_file = open('/Reine/models/Letter+x+Numbermodel-architecture.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    letter_x_number = model_from_json(loaded_model_json)
    letter_x_number.load_weights('/Reine/models/Letter+x+Numbermodel_weights.h5')

    #function to run machine learning models with constraints
    #format for result lists: 
    #1 outer list containing all moves --> 
    #a inner lists, each containing one ply --> 
    #b inner inner lists, each containing probabilities for 24 classes (one class for each possible character)
    #where a=number of moves, and b=number of boxes in each move that actually contains writing
    
    mapping = '012345678BKNQRabcdefgh-'
    #mapping includes 0 and - to account for castling.
    
    def identify_chars(move):
        #prediction list for a single ply
        prediction = []
        
        #Each function here accounts for the mapping as defined above, and adds 0's to the mappings where the box for which
        #that model is used for cannot possibly be a set of characters.
        #For example, the number_model predicts digits only, since the last box of any move MUST be a number when ignoring checks.
        #Then, zero probabilities are added for all other possible mappings.
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
        
        #This is where much of the optimization comes in. 
        #If move is 2 chars long, it must be a pawn moving to a new square, i.e. b4.
        #Thus, use lowercase letters and numbers only for the 2 boxes, respectively.
        #Append the probabilities as a list to the prediction list for this move.
        if len(move) == 2:
            first = pawn_model(move[0])
            second = number_model(move[1])

            prediction.append(first.tolist())
            prediction.append(second.tolist())
            
        #If move is 3 chars long, it must be a piece moving to a new square, i.e. Nf3 - OR castling.
        #Thus, use pieces, letters, and numbers only for the 3 boxes, respectively.
        #Check for castling by operating number model on third box first, if 0, use number model on first box to verify that            it's also a 0.
        #Append the probabilities as a list to the prediction list for this move.
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
        
        #If move is 4 chars long, must be either pawn capture / piece capture i.e. bxf3 or Nxf3,
        #OR non-capture piece move with specifier, which is when there are multiple possibilities for a pawn or piece to                capture on a square. i.e. Rac1.
        #Thus, check both pieces and letters for box 1. Check both letters and "x" for box 2. Last 2 boxes are letter and              number, as usual.
        #Append the probabilities as a list to the prediction list for this move.
        elif len(move) == 4:
            first = piece_letter_model(move[0])
            second = letter_x_number_model(move[1])
            third = pawn_model(move[2])
            fourth = number_model(move[3])

            prediction.append(first.tolist())
            prediction.append(second.tolist())
            prediction.append(third.tolist())
            prediction.append(fourth.tolist())
        
        
        
        #If move is 5 chars long, must be a Piece/pawn capture with specifier, i.e. Raxc1, b2xf3.
        #Verify castle by running number model on box 5, then box 1, then box 3.
        #Otherwise, run box 1=Letter+piece model, box 2=Number+x+letter model, box 3="x", box 4=letter, boxes 5=number
        #Append the probabilities as a list to the prediction list for this move.
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
        #Outermost list to which move predictions from the above functions are appended to
        predictions = []
        pop = 0
        done = False

        while not done:
            move = []
            #Loop through 1 ply each time (5 boxes), if mean pixel value after thresholding is less than 3, ignore box.
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
            #Box population counter, when 500 is reached (total number of boxes on scoresheet), complete function.
            pop += 5
            if pop == 500:
                done = True

        return predictions

    return read_game(imgs)
