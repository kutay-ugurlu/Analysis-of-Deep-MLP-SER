# lstm_lstm: emotion recognition from speech= lstm, text=lstm
# created for ATSIT paper 2020
# coded by Bagus Tris Atmaja (bagus@ep.its.ac.id)
# %%
import os
import json
from sklearn.model_selection import train_test_split
import numpy as np
import random as rn
import pandas as pd

from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.neural_network import MLPRegressor
from calc_scores import calc_scores

rn.seed(123)
np.random.seed(99)

# loading file and label
feat_train = np.load('../data/feat_hfs_gemaps_msp_train.npy')
feat_test = np.load('../data/feat_hfs_gemaps_msp_test.npy')

feat = np.vstack([feat_train, feat_test])


# %%
list_path = '../data/improv_data.csv'
list_file = pd.read_csv(list_path, index_col=None)
data = list_file.sort_values(by=['wavfile'])

vad_train = []
vad_test = []

for index, row in data.iterrows():
    #print(row['wavfile'], row['v'], row['a'], row['d'])
    if int(row['wavfile'][18]) in range(1, 6):
        #print("Process vad..", row['wavfile'])
        vad_train.append([row['v'], row['a'], row['d']])
    else:
        #print("Process..", row['wavfile'])
        vad_test.append([row['v'], row['a'], row['d']])

vad = np.vstack([vad_train, vad_test])

# standardization
scaled_feature = True

if scaled_feature == True:
    scaler = StandardScaler()
    scaler = scaler.fit(feat)
    scaled_feat = scaler.transform(feat)
    feat = scaled_feat
else:
    feat = feat

scaled_vad = True

# standardization
if scaled_vad:
    scaler = MinMaxScaler(feature_range=(-1, 1))
    # .reshape(vad.shape[0]*vad.shape[1], vad.shape[2]))
    scaler = scaler.fit(vad)
    # .reshape(vad.shape[0]*vad.shape[1], vad.shape[2]))
    scaled_vad = scaler.transform(vad)
    vad = scaled_vad
else:
    vad = vad

# %%
# train/test split, LOSO
X_train = feat[:len(feat_train)]
X_test = feat[len(feat_train):]
y_train = vad[:len(vad_train)]
y_test = vad[len(vad_train):]


# %%

# batch_size=min(200, n_samples)
# layers (256, 128, 64, 32, 16)
nn = MLPRegressor(
    hidden_layer_sizes=(256, 256, 128, 64, 32, 16), activation='logistic', solver='adam', alpha=0.001,
    learning_rate='constant', learning_rate_init=0.001, power_t=0.5, max_iter=180, shuffle=True,
    random_state=1, verbose=1, warm_start=False,
    early_stopping=True, validation_fraction=0.2, beta_1=0.9, beta_2=0.999, epsilon=1e-08,
    n_iter_no_change=10)

nn = nn.fit(X_train, y_train)
y_predict = nn.predict(X_test)

ccc = []
for i in range(0, 3):
    ccc_, _, _ = calc_scores(y_predict[:, i], y_test[:, i])
    ccc.append(ccc_)
    # print("# ", ccc)

print(ccc)
print(np.mean(ccc))

## MODIFICATIONS

data = {}

data["First Eval"] = np.mean(ccc)


TEST_DATA = np.load(
    "../data/MELDRaw/MELD_test_data_no_neutral.npy")
TEST_LABEL = np.load(
    "../data/MELDRaw/MELD_labels_no_neutral.npy")
TRAIN_DATA = np.load(
    "../data/MELDRaw/MELD_train_data_no_neutral.npy")
TRAIN_LABEL = np.load(
    "../data/MELDRaw/MELD_labels_no_neutral_train.npy")
print(TRAIN_LABEL)

scaled_feature = True

if scaled_feature == True:
    scaler = StandardScaler()
    scaler = scaler.fit(TEST_DATA)
    scaled_feat = scaler.transform(TEST_DATA)
    val_data_2 = scaled_feat
else:
    val_data_2 = TEST_DATA

if scaled_feature == True:
    scaler = StandardScaler()
    scaler = scaler.fit(TRAIN_DATA)
    scaled_feat = scaler.transform(TRAIN_DATA)
    val_data_2 = scaled_feat
else:
    val_data_2 = TRAIN_DATA

scaled_vad = False

# standardization
if scaled_vad:
    scaler = MinMaxScaler(feature_range=(-1, 1))
    # .reshape(vad.shape[0]*vad.shape[1], vad.shape[2]))
    scaler = scaler.fit(vad)
    # .reshape(vad.shape[0]*vad.shape[1], vad.shape[2]))
    scaled_vad = scaler.transform(vad)
    vad = scaled_vad
else:
    vad = vad

y_predict = nn.predict(TEST_DATA)


ccc = []
for i in range(0, 3):
    ccc_, _, _ = calc_scores(y_predict[:, i], TEST_LABEL[:, i])
    ccc.append(ccc_)
    # print("# ", ccc)

data["Second Eval"] = np.mean(ccc)
data["Second Eval whole"] = ccc


nn = MLPRegressor(
    hidden_layer_sizes=(256, 128, 64, 32, 16),  activation='logistic', solver='adam', alpha=0.001, batch_size='auto',
    learning_rate='constant', learning_rate_init=0.001, power_t=0.5, max_iter=500, shuffle=True,
    random_state=9, verbose=1, warm_start=True, momentum=0.9, nesterovs_momentum=True,
    early_stopping=True, validation_fraction=0.2, beta_1=0.9, beta_2=0.999, epsilon=1e-08,
    n_iter_no_change=250)



X_train = TRAIN_DATA
X_test = TEST_DATA
y_train = TRAIN_LABEL
y_test = TEST_LABEL

nn = nn.fit(X_train, y_train)
y_predict = nn.predict(X_test)


ccc = []
for i in range(0, 3):
    ccc_, _, _ = calc_scores(y_predict[:, i], y_test[:, i])
    ccc.append(ccc_)
    # print("# ", ccc)

data["Third Eval"] = np.mean(ccc)


script_name = os.path.basename(__file__)
with open('JSONs/' + script_name + '_data.json', 'w') as f:
    json.dump(data, f)

# Results:
#  0.3347105262468933
#  0.5823825252355231
#  0.4583157685040692
