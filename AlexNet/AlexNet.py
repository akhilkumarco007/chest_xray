"""
Copyright 2017-2022 Department of Electrical and Computer Engineering
University of Houston, TX/USA
**********************************************************************************
Author:   Aryan Mobiny
Date:     6/1/2017
Comments: AlexNet implementation for Chest X-ray data set.

The general structure of the network is similar to the network used in the original
paper: "ImageNet Classification with Deep Convolutional Neural Networks" by Alex Krizhevsky,et. al, 
of course with changes in the network parameters such as the number of convolutional layer filters, 
kernel sizes, etc. to make it compatible with our data.
To use it with your own data, feel free to change the parameters such as kernel sizes, strides, etc.
**********************************************************************************
"""

import tensorflow as tf
from ops import *
from utils import *


class Alexnet:
    # Class properties
    __network = None         # Graph for AlexNet
    __train_op = None        # Operation used to optimize loss function
    __loss = None            # Loss function to be optimized, which is based on predictions
    __accuracy = None        # Classification accuracy for all conditions
    __probs = None           # Prediction probability matrix of shape [batch_size, numClasses]

    def __init__(self, numClass, imgSize, imgChannel):
        self.imgSize = imgSize
        self.numClass = numClass
        self.imgChannel = imgChannel
        self.h1 = 100		# Number of neurons in the first fully-connected layer
        self.h2 = 50		# Number of neurons in the second fully-connected layer
        self.lmbda = 5e-04  # weight decay
        self.init_lr = 0.001	# Initial learning rate
        self.x, self.y, self.keep_prob = self.create_placeholders()

    def create_placeholders(self):
        with tf.name_scope('Input'):
            x = tf.placeholder(tf.float32, shape=(None, self.imgSize, self.imgSize, self.imgChannel),
                              name='x-input')
            y = tf.placeholder(tf.float32, shape=(None, self.numClass), name='y-input')
            keep_prob = tf.placeholder(tf.float32)
        return x, y, keep_prob

    def inference(self):
        if self.__network:
            return self
        # Building network...
        with tf.variable_scope('AlexNet'):
            net = conv_2d(self.x, 4, 1, 16, 'CONV1', add_reg=False, use_relu=True)
            net = max_pool(net, 2, 2, 'MaxPool1')
            net = lrn(net, 2, 2e-05, 0.75, name='norm1')
            net = conv_2d(net, 3, 1, 32, 'CONV2', add_reg=False, use_relu=True)
            net = max_pool(net, 2, 2, 'MaxPool2')
            net = lrn(net, 2, 2e-05, 0.75, name='norm2')
            net = conv_2d(net, 3, 1, 64, 'CONV3', add_reg=False, use_relu=True)
            net = conv_2d(net, 3, 1, 64, 'CONV4', add_reg=False, use_relu=True)
            net = conv_2d(net, 3, 1, 64, 'CONV5', add_reg=False, use_relu=True)
            net = max_pool(net, 2, 2, 'MaxPool3')
            layer_flat = flatten_layer(net)
            net = fc_layer(layer_flat, self.h1, 'FC1', add_reg=False, use_relu=True)
            net = dropout(net, self.keep_prob)
            net = fc_layer(net, self.h2, 'FC2', add_reg=False, use_relu=True)
            net = dropout(net, self.keep_prob)
            net = fc_layer(net, self.numClass, 'FC3', add_reg=False, use_relu=False)
            self.__network = net
        return self

    def pred_func(self):
        if self.__probs:
            return self
        self.__probs = tf.nn.softmax(self.__network)
        return self

    def accuracy_func(self):
        if self.__accuracy:
            return self
        with tf.name_scope('Accuracy'):
            self.__accuracy = accuracy_generator(self.y, self.__network)
        return self

    def loss_func(self):
        if self.__loss:
            return self
        with tf.name_scope('Loss'):
            with tf.name_scope('cross_entropy'):
                cross_entropy = cross_entropy_loss(self.y, self.__network, self.pos_weights)
                tf.summary.scalar('cross_entropy', cross_entropy)
            with tf.name_scope('l2_loss'):
                l2_loss = tf.reduce_sum(
                    self.lmbda * tf.stack([tf.nn.l2_loss(v) for v in tf.get_collection('reg_weights')]))
                tf.summary.scalar('l2_loss', l2_loss)
            with tf.name_scope('total'):
                self.__loss = cross_entropy + l2_loss
        return self

    def train_func(self):
        if self.__train_op:
            return self
        with tf.name_scope('Train'):
            optimizer = tf.train.AdamOptimizer(learning_rate=self.init_lr)
            self.__train_op = optimizer.minimize(self.__loss)
        return self

    @property
    def network(self):
        return self.__network

    @property
    def probs(self):
        return self.__probs

    @property
    def train_op(self):
        return self.__train_op

    @property
    def loss(self):
        return self.__loss

    @property
    def accuracy(self):
        return self.__accuracy
