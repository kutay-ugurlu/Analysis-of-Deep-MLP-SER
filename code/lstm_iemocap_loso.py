# CSL Paper: Dimensional speech emotion recognition from acoustic and text
# Changelog:
# 2019-09-01: initial version
# 2019-10-06: optimizer MTL parameters with linear search (in progress)
# 2012-12-25: modified fot ser_iemocap_loso_hfs.py
#             feature is either std+mean or std+mean+silence (uncomment line 44)

import os
import json
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
import numpy as np
import pickle
import pandas as pd

import keras.backend as K
from keras.models import Model
from keras.layers import Input, Dense, LSTM, Flatten, \
    Embedding, Dropout, BatchNormalization, \
    RNN, concatenate, Activation

from keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler, MinMaxScaler

from keras.preprocessing.text import Tokenizer
from keras.preprocessing import sequence

import random as rn
import tensorflow as tf


rn.seed(123)
np.random.seed(99)
tf.compat.v1.set_random_seed(1234)

# load feature and labels
feat = np.load('../data/feat_ws_3.npy')
vad = np.load('../data/y_egemaps.npy')

# for LSTM input shape (batch, steps, features/channel)
feat = feat.reshape(feat.shape[0], 1, feat.shape[1])

# remove outlier, < 1, > 5
vad = np.where(vad == 5.5, 5.0, vad)
vad = np.where(vad == 0.5, 1.0, vad)

# standardization
scaled_feature = True

# set Dropout
do = 0.3

if scaled_feature == True:
    scaler = StandardScaler()
    scaler = scaler.fit(feat.reshape(
        feat.shape[0]*feat.shape[1], feat.shape[2]))
    scaled_feat = scaler.transform(feat.reshape(
        feat.shape[0]*feat.shape[1], feat.shape[2]))
    scaled_feat = scaled_feat.reshape(
        feat.shape[0], feat.shape[1], feat.shape[2])
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

# Concordance correlation coefficient (CCC)-based loss function - using non-inductive statistics


def ccc(gold, pred):
    gold = K.squeeze(gold, axis=-1)
    pred = K.squeeze(pred, axis=-1)
    gold_mean = K.mean(gold, axis=-1, keepdims=True)
    pred_mean = K.mean(pred, axis=-1, keepdims=True)
    covariance = (gold-gold_mean)*(pred-pred_mean)
    gold_var = K.mean(K.square(gold-gold_mean), axis=-1,  keepdims=True)
    pred_var = K.mean(K.square(pred-pred_mean), axis=-1, keepdims=True)
    ccc = K.constant(2.) * covariance / (gold_var + pred_var +
                                         K.square(gold_mean - pred_mean) + K.common.epsilon())
    return ccc


def ccc_loss(gold, pred):
    # input (num_batches, seq_len, 1)
    ccc_loss = K.constant(1.) - ccc(gold, pred)
    return ccc_loss


# API model, if use RNN, first two rnn layer must return_sequences=True
def api_model(alpha, beta, gamma):
    # speech network
    input_speech = Input(
        shape=(feat.shape[1], feat.shape[2]), name='speech_input')
    net_speech = BatchNormalization()(input_speech)
    net_speech = LSTM(256, return_sequences=True)(net_speech)
    net_speech = LSTM(128, return_sequences=True)(net_speech)
    net_speech = LSTM(64, return_sequences=True)(net_speech)
    net_speech = LSTM(32, return_sequences=True)(net_speech)
    net_speech = LSTM(16, return_sequences=True)(net_speech)
    model_speech = Flatten()(net_speech)
    #model_speech = Dropout(0.1)(net_speech)

    target_names = ('v', 'a', 'd')
    model_combined = [Dense(1, name=name)(model_speech)
                      for name in target_names]

    model = Model(input_speech, model_combined)
    #model.compile(loss=ccc_loss, optimizer='rmsprop', metrics=[ccc])
    model.compile(loss=ccc_loss,
                  loss_weights={'v': alpha, 'a': beta, 'd': gamma},
                  optimizer='adam', metrics=[ccc])
    return model


# def main(alpha, beta, gamma):
model = api_model(0.1, 0.5, 0.4)
model.summary()

# 7869 first data of session 5 (for LOSO)
earlystop = EarlyStopping(monitor='val_loss', mode='min', patience=10,
                          restore_best_weights=True)
hist = model.fit(feat[:7869], vad[:7869].T.tolist(), batch_size=200,  # best:8
                 validation_split=0.2, epochs=180, verbose=1, shuffle=True,
                 callbacks=[earlystop])
metrik = model.evaluate(feat[7869:], vad[7869:].T.tolist())
print(metrik)


## MODIFICATIONS

data = {}

data["First Eval"] = np.mean(metrik[-3:])


TEST_DATA = np.load(
    "../data/MELDRaw/MELD_test_data_no_neutral.npy")
TEST_LABEL = np.load(
    "../data/MELDRaw/MELD_labels_no_neutral.npy")
TRAIN_DATA = np.load(
    "../data/MELDRaw/MELD_train_data_no_neutral.npy")
TRAIN_LABEL = np.load(
    "../data/MELDRaw/MELD_labels_no_neutral_train.npy")


TEST_DATA = TEST_DATA.reshape(TEST_DATA.shape[0], TEST_DATA.shape[1], 1)
TRAIN_DATA = TRAIN_DATA.reshape(TRAIN_DATA.shape[0], TRAIN_DATA.shape[1], 1)

scaled_feature = True

if scaled_feature == True:
    scaler = StandardScaler()
    scaler = scaler.fit(TEST_DATA.reshape(
        TEST_DATA.shape[0]*TEST_DATA.shape[1], TEST_DATA.shape[2]))
    scaled_feat = scaler.transform(TEST_DATA.reshape(
        TEST_DATA.shape[0]*TEST_DATA.shape[1], TEST_DATA.shape[2]))
    scaled_feat = TEST_DATA.reshape(
        TEST_DATA.shape[0], TEST_DATA.shape[1], TEST_DATA.shape[2])
    TEST_DATA = scaled_feat
else:
    TEST_DATA = TEST_DATA

if scaled_feature == True:
    scaler = StandardScaler()
    scaler = scaler.fit(TRAIN_DATA.reshape(
        TRAIN_DATA.shape[0]*TRAIN_DATA.shape[1], TRAIN_DATA.shape[2]))
    scaled_feat = scaler.transform(TRAIN_DATA.reshape(
        TRAIN_DATA.shape[0]*TRAIN_DATA.shape[1], TRAIN_DATA.shape[2]))
    scaled_feat = TRAIN_DATA.reshape(
        TRAIN_DATA.shape[0], TRAIN_DATA.shape[1], TRAIN_DATA.shape[2])
    TRAIN_DATA = scaled_feat
else:
    TRAIN_DATA = TRAIN_DATA


scaled_vad = False

# standardization
if scaled_vad:
    scaler = MinMaxScaler(feature_range=(-1, 1))
    # .reshape(vad.shape[0]*vad.shape[1], vad.shape[2]))
    scaler = scaler.fit(TEST_LABEL)
    # .reshape(vad.shape[0]*vad.shape[1], vad.shape[2]))
    scaled_vad = scaler.transform(TEST_LABEL)
    TEST_LABEL = scaled_vad
else:
    TEST_LABEL = TEST_LABEL

TEST_DATA = np.transpose(TEST_DATA, axes=[0, 2, 1])
TRAIN_DATA = np.transpose(TRAIN_DATA, axes=[0, 2, 1])


val_list = np.transpose(TEST_LABEL).tolist()


# Test with first model
metrik_val = model.evaluate(TEST_DATA, val_list)
print(metrik_val)
print("Second Eval CCC ave= ", np.mean(metrik_val[-3:]))
data["Second Eval"] = np.mean(metrik_val[-3:])
data["Second Eval whole"] = metrik_val[-3:]


X_train = TRAIN_DATA
X_test = TEST_DATA
y_train = TRAIN_LABEL
y_test = TEST_LABEL

model = api_model(0.1, 0.5, 0.4)
earlystop = EarlyStopping(monitor='val_loss', mode='min', patience=100,
                          restore_best_weights=True)
hist = model.fit(X_train, np.transpose(y_train).tolist(), batch_size=200,  # best:8
                 validation_split=0.2, epochs=180, verbose=2, shuffle=True,
                 callbacks=[earlystop])
metrik_val = model.evaluate(X_test, val_list)
print(metrik_val)
print("Third Eval CCC ave= ", np.mean(metrik_val[-3:]))
data["Third Eval"] = np.mean(metrik_val[-3:])


script_name = os.path.basename(__file__)
with open('JSONs/' + script_name + '_data.json', 'w') as f:
    json.dump(data, f)


# save prediction, comment to avoid overwriting
#predict = model.predict(feat[6296:], batch_size=200)
# np.save('../data/predict_lstm_iemocap_sd',
#         np.array(predict).reshape(3, 3743).T)
