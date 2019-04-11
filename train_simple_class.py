# -*- coding: utf-8 -*-
"""
Residual Attention Network
"""

import numpy as np
import time

from sklearn.utils import shuffle
from sklearn.metrics import f1_score, accuracy_score
import tensorflow as tf
from tqdm import tqdm
import utils
from model.utils import EarlyStopping
from model.residual_attention_network_1 import ResidualAttentionNetwork
from hyperparameter import HyperParams as hp
import os
import keras

os.environ['CUDA_VISIBLE_DEVICES'] = '6'

import h5py
import scipy.misc
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import SimpleITK as sitk


def plot_conv_output(conv_img, plot_dir, name, filters_all=True, filters=[0]):
    w_min = np.min(conv_img)
    w_max = np.max(conv_img)
    
    # get number of convolutional filters
    if filters_all:
        num_filters = conv_img.shape[3]
        filters = range(conv_img.shape[3])
    else:
        num_filters = len(filters)
    
    # get number of grid rows and columns
    grid_r, grid_c = utils.get_grid_dim(num_filters)
    
    # create figure and axes
    fig, axes = plt.subplots(min([grid_r, grid_c]),
                             max([grid_r, grid_c]))
    
    # iterate filters
    if num_filters == 1:
        img = conv_img[0, :, :, filters[0]]
        axes.imshow(img, vmin=w_min, vmax=w_max, interpolation='bicubic', cmap=cm.hot)
        # remove any labels from the axes
        axes.set_xticks([])
        axes.set_yticks([])
    else:
        for l, ax in enumerate(axes.flat):
            # get a single image
            img = conv_img[0, :, :, filters[l]]
            # put it on the grid
            ax.imshow(img, vmin=w_min, vmax=w_max, interpolation='bicubic', cmap=cm.hot)
            # remove any labels from the axes
            ax.set_xticks([])
            ax.set_yticks([])
    # save figure
    print(os.path.join(plot_dir, '{}.png'.format(name)))
    plt.savefig(os.path.join(plot_dir, '{}.png'.format(name)), bbox_inches='tight')


if __name__ == "__main__":
    print("start to train ResidualAttentionModel")
    print('tensorflow_version', tf.__version__)
    print('keras version', keras.__version__)
    num = 5
    train_X, train_y_class, train_y_seg, valid_X, valid_y_class, valid_y_seg, test_X, test_y, test_class_y = utils.load_data_new_dcm_128(num)
    
    print("build graph...")
    model = ResidualAttentionNetwork()
    early_stopping = EarlyStopping(limit=20)
    
    x = tf.placeholder(tf.float32, [None, 128, 128, 1], name='x')
    # t_seg = tf.placeholder(tf.float32, [None, 128, 128, 2])
    t_class = tf.placeholder(tf.float32, [None, 2])
    
    # lr = tf.Variable(0.01, dtype=tf.float32)
    
    is_training = tf.placeholder(tf.bool, shape=())
    y_class = model.f_prop(x)
    
    # loss = tf.nn.softmax_cross_entropy_with_logits(logits=y, labels=t)
    # 交叉熵
    # loss_class = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=y_class, labels=t_class))
    # loss_seg = tf.reduce_mean(-tf.reduce_sum(t_seg * tf.log(y_seg + 1e-7), reduction_indices=[1]))
    loss_class = tf.reduce_mean(-tf.reduce_sum(t_class * tf.log(y_class + 1e-7), reduction_indices=[1]))
    
    # loss_seg = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=y_seg, labels=t_seg))
    # loss_join = loss_class + loss_seg
    
    adam_class = tf.train.AdamOptimizer(1e-5).minimize(tf.reduce_mean(loss_class))
    # adam_seg = tf.train.AdamOptimizer(1e-3).minimize(tf.reduce_mean(loss_seg))
    # adam_join = tf.train.AdamOptimizer(1e-5).minimize(tf.reduce_mean(loss_join))
    
    valid_class = tf.argmax(y_class, 1)
    # valid_seg = tf.argmax(y_seg, 1)
    
    print("check shape of data...")
    print("train_X: {shape}".format(shape=train_X.shape))
    print("train_y_class: {shape}".format(shape=train_y_class.shape))
    # print("train_y_seg: {shape}".format(shape=train_y_seg.shape))
    
    print("start to train...")
    with tf.Session() as sess:
        init = tf.global_variables_initializer()
        # init = initialize_all_variables()
        sess.run(init)
        i_cout = 0
        for epoch in range(hp.NUM_EPOCHS_HEART):
            train_X, train_y_class = shuffle(train_X, train_y_class,
                                                          random_state=hp.RANDOM_STATE)
            # batch_train_X, batch_valid_X, batch_train_y, batch_valid_y = train_test_split(train_X, train_y, train_size=0.8, random_state=random_state)
            n_batches = train_X.shape[0] // hp.BATCH_SIZE_HEART
            
            # one-hot test 图像显示
            # one_hot_itk_arr = train_y_seg[6]
            # one_hot_itk_arr = np.transpose(one_hot_itk_arr, (2, 1, 0))
            #
            # a = one_hot_itk_arr[0, :, :]
            # b = one_hot_itk_arr[1, :, :]
            # CT_predict_itka = sitk.GetImageFromArray(a)
            # CT_predict_itkb = sitk.GetImageFromArray(b)
            # main_path = '/home/luochao/project/Data/Heart/MutiTask'
            # sitk.WriteImage(CT_predict_itka, main_path + '/predict/' + 'testa' + 'PredictResult.mha')
            # sitk.WriteImage(CT_predict_itkb, main_path + '/predict/' + 'testb' + 'PredictResult.mha')
            
            # train
            train_costs = []
            for i in (range(n_batches)):
                # print(i)
                start = i * hp.BATCH_SIZE_HEART
                end = start + hp.BATCH_SIZE_HEART
                # print('start',start)
                # print('end', end)
                # print('train_X.shape',train_X.shape)
                # print('train_Y.shape',train_y.shape)
                # print('train_X[start:end]',train_X[start:end].shape)
                # print('train_y[start:end]',train_y[start:end].shape)
                # data = train_X[start:end]
                # print('data.shape',data.shape)
                # print('train_y[start:end]',train_y[start:end].shape)
                # image = data[0].transpose(2, 1, 0)
                # image = data[0]
                
                # print('image.shape',image.shape)
                # CT_predict_itk = sitk.GetImageFromArray(image)
                # CT_predict_itk.SetOrigin((-110.853, -76.4994, -68.8995))
                # CT_predict_itk.SetSpacing((1.0, 1.0, 1.0))
                # CT_predict_itk.SetDirection((1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
                #
                # sitk.WriteImage(CT_predict_itk, '/home/luochao/project/residual-attention-network/ori_image/' + str(
                #     epoch) + 'Result.mha')
                
                # if epoch<= 100:
                #     sess.run(tf.assign(lr, 1e-3))
                # else:
                #     sess.run(tf.assign(lr, 1e-5))
                
                _, _loss = sess.run([adam_class, loss_class],
                                    feed_dict={x: train_X[start:end], t_class: train_y_class[start:end], is_training: True})
                
                # print ('_loss', _loss)
                # print('_loss_seg', _loss_seg)
                #
                # print('loss_class', _loss_class)
                
                train_costs.append(_loss)
            
            print('************ Epoch **********:', epoch)
            
            # learning_rate = sess.run(lr)
            # print('*********** learning_rate *************', learning_rate)
            # valids
            valid_costs = []
            valid_predictions_class = []
            valid_predictions_seg = []
            n_batches = valid_X.shape[0] // hp.VALID_BATCH_SIZE_HEART
            for i in range(n_batches):
                start = i * hp.VALID_BATCH_SIZE_HEART
                end = start + hp.VALID_BATCH_SIZE_HEART
                # pred_class, valid_cost1 = sess.run([valid_class, loss_class], feed_dict={x: valid_X[start:end], t_class: valid_y_class[start:end],
                #                                                        is_training: False})
                # pred_seg, valid_cost2 = sess.run([y_seg, loss_seg],
                #                             feed_dict={x: valid_X[start:end], t_seg: valid_y_seg[start:end],
                #                                        is_training: False})
                
                pred_class, _loss = sess.run([y_class, loss_class],
                                                       feed_dict={x: valid_X[start:end],
                                                                  t_class: valid_y_class[start:end],
                                                                  is_training: False})
                pred_class = np.argmax(pred_class, 1)
                valid_predictions_class.extend(pred_class)
                
                valid_costs.append(_loss)
            
            # f1_score = f1_score(np.argmax(valid_y, 1).astype('int32'), valid_predictions, average='macro')
            accuracy_class = accuracy_score(np.argmax(valid_y_class, 1).astype('int32'), valid_predictions_class)
            # accuracy_seg = accuracy_score(valid_y_seg, valid_predictions_seg)
            # if epoch % 5 == 0:
            #     print('EPOCH: {epoch}, Training cost: {train_cost}, Validation cost: {valid_cost}, Validation Accuracy: {accuracy} '
            #           .format(epoch=epoch, train_cost=np.mean(train_costs), valid_cost=np.mean(valid_costs), accuracy=accuracy))
            print(
            'EPOCH: {epoch}, Training cost: {train_cost}, Validation cost: {valid_cost}, Validation Class Accuracy: {accuracy_class}'
                .format(epoch=epoch, train_cost=np.mean(train_costs), valid_cost=np.mean(valid_costs),
                        accuracy_class=accuracy_class))
            # if early_stopping.check(np.mean(valid_costs)):
            #     break
        
        print("save model...")
        save_path = hp.HOME_DIR + "trained_models_" + str(num)
        if not os.path.exists(save_path):
            os.mkdir(save_path)
        save_path = save_path + "/model.ckpt"
        saver = tf.train.Saver()
        saver.save(sess, save_path, global_step=epoch)


