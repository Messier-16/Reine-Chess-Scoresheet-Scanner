import csv

onechar=0
twochar=0
threechar=0
fourchar=0
fivechar=0
sixchar=0
sevenchar=0
eightchar=0
queens=0
nonqueens=0
queenside=0
kingside=0
moves=0
chars=0
games=0
with open('/Users/RithwikSudharsan 1/PycharmProjects/pythontest/Reine/chess move data - Sheet1.csv', newline='') as csvfile:
    movereader = csv.reader(csvfile, delimiter=' ')
    for row in movereader:
        games+=1
        for move in row:
            moves+=1
            chars+=len(move)
            if 'O-O' in move:
                kingside+=1
            if 'O-O-O' in move:
                queenside+=1
            length=len(move)
            if length==1:
                onechar+=1
            elif length==2:
                twochar+=1
            elif length==3:
                threechar+=1
            elif length==4:
                fourchar+=1
            elif length==5:
                fivechar+=1
            elif length==6:
                sixchar+=1
            elif length==7:
                sevenchar+=1
            elif length==8:
                eightchar+=1
            if '=' in move:
                if '=Q' in move:
                    queens+=1
                else:
                    nonqueens+=1




totalpromotions=queens+nonqueens
total=onechar+twochar+threechar+fourchar+fivechar+sixchar+sevenchar+eightchar
totalcastle=kingside+queenside
print(onechar/total,twochar/total,threechar/total,fourchar/total,fivechar/total,sixchar/total,sevenchar/total,eightchar/total)
print(queens/totalpromotions,nonqueens/totalpromotions)
print(kingside/totalcastle,queenside/totalcastle)

print(moves/games/2)
print(chars/moves)


