import pandas as pd
import time

start = time.time()
file = 'C:/Users/alexf/Desktop/reine/emnist/emnist-byclass-train.csv'
chunk = pd.read_csv(file, chunksize=50000, nrows=500)
data = pd.concat(chunk)
print(data[499:500])
end = time.time()
print('Time: ' + str(end - start) + ' s')
