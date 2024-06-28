# Reine
by Rithwik Sudharsan and Alex Fung

This product scans chess scoresheets, but as per suggestions can be modified to work on other forms for processing. Open-sourced under the GPL license.

Website here: https://omcgov.wixsite.com/reine

Chess.com article here, describing roughly how this works: https://www.chess.com/blog/ReineChess/scannable-scoresheets-free

Show HackerNews post here: https://news.ycombinator.com/item?id=19162876

We thank [Marek Śmigielski's post here](https://medium.com/@mareksmigielski/from-chess-score-sheet-to-icr-with-opencv-and-image-recognition-f7bed2cc3de4) for the alignment algorithm and a general perspective on how we could solve this problem, another developer who attempted the same idea. Lots of Kaggle kernels, other Medium articles, and StackOverflow posts obviously helped too.

![alt text](https://images.chesscomfiles.com/uploads/v1/blog/354692.06eee19c.630x354o.f755445341aa@2x.png)

How it works:
1. Take picture
![alt text](https://images.chesscomfiles.com/uploads/v1/images_users/tiny_mce/ReineChess/phpYAXkpl.jpeg)
2. Align scoresheet
![alt text](https://images.chesscomfiles.com/uploads/v1/images_users/tiny_mce/ReineChess/phpaNPWKy.png)
3. Cut up scoresheet into boxes
![alt text](https://images.chesscomfiles.com/uploads/v1/images_users/tiny_mce/ReineChess/php3hSQwk.png)
4. Preprocess boxes to look like EMNIST data
5. Run boxes through CNN to get predictions
6. Postprocess results by checking every combination of top 2 most likely characters for each box, looking for valid games.      This way, as long as the correct characters are all in the top 2 predictions for each box, the game should be found.
7. Download .pgn file (or .txt if complete game wasn't found, then edit and change to .pgn)
![alt text](https://images.chesscomfiles.com/uploads/v1/images_users/tiny_mce/ReineChess/phpbCvFaT.png)
8. Open in your engine of choice and analyze!
![alt text](https://images.chesscomfiles.com/uploads/v1/images_users/tiny_mce/ReineChess/php0jChmT.png)
