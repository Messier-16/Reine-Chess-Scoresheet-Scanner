# Reine: Chess Scoresheet Scanner

### By Rithwik Sudharsan and Alex Fung

**Reine** is a high-accuracy, open-source tool for scanning chess scoresheets, which can be modified to process other types of form data as well. This project is licensed under the [GPL License](LICENSE).

### Overview

Reine takes an image of a chess scoresheet, processes it to recognize and align text, and outputs a Portable Game Notation (.pgn) file, which can then be analyzed in popular chess engines. This tool was inspired by and partially based on the work of Marek Śmigielski and others in the open-source community. 

![Sample Scoresheet](https://images.chesscomfiles.com/uploads/v1/blog/354692.06eee19c.630x354o.f755445341aa@2x.png)

---

### Key Links

- **Website**: [Reine Homepage](https://omcgov.wixsite.com/reine)
- **Chess.com article**: [Scannable Chess Scoresheets](https://www.chess.com/blog/ReineChess/scannable-scoresheets-free)
- **Show HN post**: [Hacker News Discussion](https://news.ycombinator.com/item?id=19162876)
- **Alignment Inspiration**: [Marek Śmigielski’s Medium Article](https://medium.com/@mareksmigielski/from-chess-score-sheet-to-icr-with-opencv-and-image-recognition-f7bed2cc3de4)

### How It Works

1. **Capture**: Take a photo of the chess scoresheet.
   
   ![Capture](https://images.chesscomfiles.com/uploads/v1/images_users/tiny_mce/ReineChess/phpYAXkpl.jpeg)

2. **Align**: Use image processing techniques to align the scoresheet.
   
   ![Align](https://images.chesscomfiles.com/uploads/v1/images_users/tiny_mce/ReineChess/phpaNPWKy.png)

3. **Segmentation**: Divide the scoresheet into individual move boxes.
   
   ![Segment](https://images.chesscomfiles.com/uploads/v1/images_users/tiny_mce/ReineChess/php3hSQwk.png)

4. **Preprocess**: Format each box to match the EMNIST dataset for optimal character recognition.

5. **Prediction**: Pass each box through a Convolutional Neural Network (CNN) to predict the characters.

6. **Validation**: Cross-check predictions by analyzing combinations of the top two character probabilities for each box to ensure a valid game sequence.

7. **Output**: Download the output as a .pgn file (or .txt if incomplete) for analysis or editing.
   
   ![Output](https://images.chesscomfiles.com/uploads/v1/images_users/tiny_mce/ReineChess/phpbCvFaT.png)

8. **Analysis**: Open the .pgn file in a chess engine of your choice to review and analyze the game.
   
   ![Analysis](https://images.chesscomfiles.com/uploads/v1/images_users/tiny_mce/ReineChess/php0jChmT.png)
