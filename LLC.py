import stable_baselines.common.policies
from stable_baselines import A2C

import fgmodule.fgenv as fgenv
import time
import numpy as np
import os
import tensorflow as tf
import pandas as pd

LLC_FEATURES = [
    'pitch-deg',  # 飞机俯仰角
    'roll-deg',  # 飞机滚转角
    'heading-deg',  # 飞机朝向
    'vsi-fpm',  # 爬升速度
    'uBody-fps',  # 飞机沿机身X轴的速度
    'vBody-fps',  # 飞机沿机身Y轴的速度
    'wBody-fps',  # 飞机沿机身Z轴的速度
    'x-accel-fps_sec',  # 飞机沿机身X轴的加速度
    'y-accel-fps_sec',  # 飞机沿机身Y轴的加速度
    'z-accel-fps_sec',  # 飞机沿机身z轴的加速度
]


LLC_GOALS = {
    'pitch-deg': 0.0,  # 飞机俯仰角
    'roll-deg': 0.0,  # 飞机滚转角
    'heading-deg': 90.0,  # 飞机朝向
    'vsi-fpm': 0.0,  # 爬升速度
    'uBody-fps': 120.0,  # 飞机沿机身X轴的速度
    'vBody-fps': 0.0,  # 飞机沿机身Y轴的速度
    'wBody-fps': 0.0,  # 飞机沿机身Z轴的速度
    'x-accel-fps_sec': 5.0,  # 飞机沿机身X轴的加速度
    'y-accel-fps_sec': 0.0,  # 飞机沿机身Y轴的加速度
    'z-accel-fps_sec': 0.0,  # 飞机沿机身z轴的加速度
}

LLC_FEATURE_BOUNDS = {
    'pitch-deg': [-90., 90.],  # 飞机俯仰角
    'roll-deg': [-180., 180.],  # 飞机滚转角
    'heading-deg': [0., 360.],  # 飞机朝向
    'vsi-fpm': [0., 10.0],  # 爬升速度
    'uBody-fps': [0., 600.],  # 飞机沿机身X轴的速度
    'vBody-fps': [-200., 200.],  # 飞机沿机身Y轴的速度
    'wBody-fps': [-200., 200.],  # 飞机沿机身Z轴的速度
    'x-accel-fps_sec': [0., 50.],  # 飞机沿机身X轴的加速度
    'y-accel-fps_sec': [-30., 30.],  # 飞机沿机身Y轴的加速度
    'z-accel-fps_sec': [-300., 300.],  # 飞机沿机身z轴的加速度
}

LLC_ACTIONS = [
    'aileron',  # 副翼 控制飞机翻滚 [-1,1]
    'elevator',  # 升降舵 控制飞机爬升 [-1,1]
    'rudder',  # 方向舵 控制飞机转弯（地面飞机方向控制） [-1,1]
    'throttle0',  # 油门0 [0,1]
    'throttle1'  # 油门1 [0,1]
    # 'flaps',  # 襟翼 在飞机起降过程中增加升力，阻力 [0,1],实测影响不大，而且有速度限制
    #TODO: 方向舵调整片
]
LLC_ACTION_BOUNDS = {
    'aileron': [-1, 1],  # 副翼 控制飞机翻滚 [-1,1] left/right
    'elevator': [-1, 1],  # 升降舵 控制飞机爬升 [-1,1] up/down
    'rudder': [-1, 1],  # 方向舵 控制飞机转弯（地面飞机方向控制） 0 /enter
    'throttle0': [0, 1],  # 油门0
    'throttle1': [0, 1],  # 油门1
    # 'flaps': [0, 0]  # 襟翼 在飞机起降过程中增加升力，阻力  Key[ / ]	Extend / retract flaps
    #TODO: 方向舵调整片
}

DATA_BOUNDS = {
    'pitch-deg': [-90., 90.],  # 飞机俯仰角
    'roll-deg': [-180., 180.],  # 飞机滚转角
    'heading-deg': [0., 360.],  # 飞机朝向
    'vsi-fpm': [0., 10.0],  # 爬升速度
    'uBody-fps': [0., 600.],  # 飞机沿机身X轴的速度
    'vBody-fps': [-200., 200.],  # 飞机沿机身Y轴的速度
    'wBody-fps': [-200., 200.],  # 飞机沿机身Z轴的速度
    'x-accel-fps_sec': [0., 50.],  # 飞机沿机身X轴的加速度
    'y-accel-fps_sec': [-30., 30.],  # 飞机沿机身Y轴的加速度
    'z-accel-fps_sec': [-300., 300.],  # 飞机沿机身z轴的加速度
    'aileron': [-1, 1],  # 副翼 控制飞机翻滚 [-1,1] left/right
    'elevator': [-1, 1],  # 升降舵 控制飞机爬升 [-1,1] up/down
    'rudder': [-1, 1],  # 方向舵 控制飞机转弯（地面飞机方向控制） 0 /enter
    'throttle0': [0, 1],  # 油门0
    'throttle1': [0, 1],  # 油门1
    'flaps': [0, 1],  # 襟翼 在飞机起降过程中增加升力，阻力  Key[ / ]	Extend / retract flaps
    #TODO: 方向舵调整片
    'a_aileron': [-1, 1],  # 副翼 控制飞机翻滚 [-1,1] left/right
    'a_elevator': [-1, 1],  # 升降舵 控制飞机爬升 [-1,1] up/down
    'a_rudder': [-1, 1],  # 方向舵 控制飞机转弯（地面飞机方向控制） 0 /enter
    'a_throttle0': [0, 1],  # 油门0
    'a_throttle1': [0, 1],  # 油门1
}


MAX_EPISODE = 1000
MAX_EP_STEPS = 200

GAMMA = 0.9
LR_A = 0.001    # learning rate for actor
LR_C = 0.01     # learning rate for critic


def get_lower_upper_bound(bounds):
    '''
    format bound dict to lower and upper array
    '''
    lower = []
    upper = []
    for key in bounds.keys():
        lower.append(bounds[key][0])
        upper.append(bounds[key][1])
    return np.array(lower, dtype=np.float), np.array(upper, dtype=np.float)


np.random.seed(2)
tf.set_random_seed(2)  # reproducible


class Actor(object):
    def __init__(self, sess, n_features, n_actions, action_bounds, lr=0.0001):
        self.sess = sess
        self.action_bounds =get_lower_upper_bound(action_bounds)
        self.action_dim = n_actions

        self.s = tf.placeholder(tf.float32, [1, n_features], "state")
        self.a = tf.placeholder(tf.float32, None, name="act")
        self.td_error = tf.placeholder(
            tf.float32, None, name="td_error")  # TD_error

        l1 = tf.layers.dense(
            inputs=self.s,
            units=100,  # number of hidden units
            activation=tf.nn.relu,
            kernel_initializer=tf.random_normal_initializer(0., .1),  # weights
            bias_initializer=tf.constant_initializer(0.1),  # biases
            name='l1'
        )

        mu = tf.layers.dense(
            inputs=l1,
            units=n_actions,  # output units
            activation=tf.nn.tanh,
            kernel_initializer=tf.random_normal_initializer(0., .1),  # weights
            bias_initializer=tf.constant_initializer(0.1),  # biases
            name='mu'
        )

        sigma = tf.layers.dense(
            inputs=l1,
            units=n_actions,  # output units
            activation=tf.nn.softplus,  # get action probabilities
            kernel_initializer=tf.random_normal_initializer(0., .1),  # weights
            bias_initializer=tf.constant_initializer(1.),  # biases
            name='sigma'
        )
        global_step = tf.Variable(0, trainable=False)
        # self.e = epsilon = tf.train.exponential_decay(2., global_step, 1000, 0.9)
        
        self.mu, self.sigma = tf.squeeze(mu), tf.squeeze(sigma)

        self.normal_dist = tf.distributions.Normal(self.mu, self.sigma)

        self.action = tf.squeeze(tf.clip_by_value(
            self.normal_dist.sample(1), self.action_bounds[0], self.action_bounds[1]))

        with tf.name_scope('exp_v'):
            log_prob = self.normal_dist.log_prob(
                self.a)  # loss without advantage
            # advantage (TD_error) guided loss
            self.exp_v = log_prob * self.td_error
            # Add cross entropy cost to encourage exploration
            self.exp_v += 0.01*self.normal_dist.entropy()

        with tf.name_scope('train'):
            self.train_op = tf.train.AdamOptimizer(
                lr).minimize(-self.exp_v, global_step)  # max(v) = min(-v)

    def learn(self, s, a, td):
        s = s[np.newaxis, :]
        feed_dict = {self.s: s, self.a: a, self.td_error: td}
        _, exp_v = self.sess.run([self.train_op, self.exp_v], feed_dict)
        return exp_v

    def choose_action(self, s):
        s = s[np.newaxis, :]
        # get probabilities for all actions
        a = self.sess.run(self.action, {self.s: s})
        return a


class Critic(object):
    def __init__(self, sess, n_features, lr=0.01, GAMMA=0.9):
        self.gamma = GAMMA
        self.sess = sess
        with tf.name_scope('inputs'):
            self.s = tf.placeholder(tf.float32, [1, n_features], "state")
            self.v_ = tf.placeholder(tf.float32, [1, 1], name="v_next")
            self.r = tf.placeholder(tf.float32, name='r')

        with tf.variable_scope('Critic'):
            l1 = tf.layers.dense(
                inputs=self.s,
                units=80,  # number of hidden units
                activation=tf.nn.relu,
                kernel_initializer=tf.random_normal_initializer(
                    0., .1),  # weights
                bias_initializer=tf.constant_initializer(0.1),  # biases
                name='l1'
            )

            self.v = tf.layers.dense(
                inputs=l1,
                units=1,  # output units
                activation=None,
                kernel_initializer=tf.random_normal_initializer(
                    0., .1),  # weights
                bias_initializer=tf.constant_initializer(0.1),  # biases
                name='V'
            )

        with tf.variable_scope('squared_TD_error'):
            self.td_error = tf.reduce_mean(
                self.r + self.gamma * self.v_ - self.v)
            # TD_error = (r+gamma*V_next) - V_eval
            self.loss = tf.square(self.td_error)
        with tf.variable_scope('train'):
            self.train_op = tf.train.AdamOptimizer(lr).minimize(self.loss)

    def learn(self, s, r, s_):
        s, s_ = s[np.newaxis, :], s_[np.newaxis, :]

        v_ = self.sess.run(self.v, {self.s: s_})
        td_error, _ = self.sess.run([self.td_error, self.train_op],
                                    {self.s: s, self.v_: v_, self.r: r})
        return td_error





class LLC():
    def __init__(self, n_features, n_actions, action_bounds, goals,actorlr=0.0001, criticlr=0.01):
        
        self.goal = goals

        
        self.features = LLC_FEATURES

        # 分别开启不同的会话
        self.actor_sess = tf.Session()
        self.critic_sess = tf.Session()

        self.actor = Actor(self.actor_sess, 2*n_features,
                              n_actions, action_bounds, actorlr)
        self.critic = Critic(self.critic_sess, 2*n_features, criticlr)

        self.saver = tf.train.Saver()
        self.actor_sess.run(tf.global_variables_initializer())
        self.critic_sess.run(tf.global_variables_initializer())

    def load(self,sess,path):
        self.saver.restore(sess, path)

    def save(self,sess,path):
        self.saver.save(sess, save_path=path)

    def choose_action(self, state , goal):
        '''
        input: 
            state(dict)
            goal(dict)
        output:
            # control frame
            # [ % f, % f, % f, % f, % f\n]
            # aileron, elevator, rudder, throttle0, throttle1
            # 副翼, 升降舵, 方向舵, 油门0, 油门1
        '''
        # 更新目标 (测试使用固定目标)
        # self.goal = goal 

        
        # 输入合并 state 和 goal
        ob = np.append(self.format_state(state),self.state2array(goal))

        action = self.actor.choose_action(ob)
        
        return action

    def learn(self, state, goal , reward, action, next_state):
        '''
        Input:
            -state(dict)
                环境返回状态
            -reward(float)
                环境提供的reward
            -action(np.array)
                agent采取的动作
            -next_state(dict)
                获取到的新状态 
        '''
        # 更新目标 (测试使用固定目标)
        # self.goal = goal
        # 输入合并 state 和 goal
        ob = np.append(self.format_state(state), self.state2array(self.goal))
        reward_ = self.cal_reward(self.norm_state(state), self.norm_state(self.goal), reward)
        next_ob = np.append(self.format_state(next_state), self.state2array(self.goal))

        # gradient = grad[r + gamma * V(s_) - V(s)]
        td_error = self.critic.learn(ob, reward_, next_ob)
        # true_gradient = grad[logPi(s,a) * td_error]

        self.actor.learn(ob, action, td_error)

        return reward_ , td_error


    def cal_reward(self, state, goal, reward):
        error = 0.0
        for key in LLC_FEATURES:
            error += ((state[key] - goal[key])**2)
        error = error/len(LLC_FEATURES)

        return reward - 0.1*error

    def format_state(self, state, dtype="array", norm = True):
        '''
        input:
            state(dict)
            dtype(str): #output dtype
                - array
                - dict
            norm(bool): # whether norm the data
        output:
            dict
        将state多余的feature筛除掉
        列表如下:
        [
            'pitch-deg', #飞机俯仰角
            'roll-deg' , #飞机滚转角
            'heading-deg' , #飞机朝向
            'vsi-fpm' ,  #爬升速度
            'uBody-fps', #飞机沿机身X轴的速度
            'vBody-fps', #飞机沿机身Y轴的速度
            'wBody-fps', #飞机沿机身Z轴的速度
            'x-accel-fps_sec', #飞机沿机身X轴的加速度
            'y-accel-fps_sec', #飞机沿机身Y轴的加速度
            'z-accel-fps_sec', #飞机沿机身z轴的加速度
        ]
        '''
        state_ = dict()
        for feature in self.features:
            state_[feature] = state[feature]

        if norm:
            state_ = self.norm_state(state_)

        if dtype == "dict":
            return state_
        if dtype == "array":
            return self.state2array(state_,False)

    def state2array(self, state , norm=True):
        '''
        input:
            state(dict)
            norm(bool): # whether norm the data
        output:
            ndarray
        将state从dict形式转换为array
        
        '''
        if norm:
            state_ = self.norm_state(state)
        state_ = np.array(list(state.values()))
        return state_

    def norm_state(self, state):
        state_ = dict()
        for feature in self.features:
            if feature == 'heading-deg':
                if state[feature] > 180.0:
                    state_[feature] = state[feature]- 360.0
                else:
                    state_[feature] = state[feature]
            bound = LLC_FEATURE_BOUNDS[feature]
            state_[feature] = state[feature] / (bound[1]-bound[0])
        return state_

    def format_action(self,action):
        '''
        input:
            -action(array)
        output:
            -action_frame(str)
                fg action frame 
        '''
        return '%f,%f,%f,%f,%f\n' % tuple(action.tolist())


    def critic_pre_train(self):
        #get train data
        pid_traindata = pd.read_csv("data/traindata/pid_traindata_sample.csv")
        data_bounds = pd.DataFrame.from_dict(DATA_BOUNDS)

        norm_traindata = ((pid_traindata - data_bounds.min()) /
                                (data_bounds.max() - data_bounds.min())).dropna(axis=1, how="any")
        #feed dict (state,target state), reward, new(state,target state)

        for i in range(norm_traindata.shape[0]-10):

            pass


'''
class HLC():
    def __init__(self):
        pass

    def choose_action(self, state, goal):

        return action

    def learn(self, state, reward, action):
        pass

    def cal_reward(self, state):

        return reward

'''

def tain_llc():
    epoch = 10000
    step = 3000
    print("client begin!")
    # input("press enter to continue!")

    ## 初始化flightgear 通信端口
    fg2client_addr = ("127.0.0.1", 5700)
    client2fg_addr = ("127.0.0.1", 5701)
    telnet_addr = ("127.0.0.1", 5555)

    # 初始化flightgear 环境
    myfgenv = fgenv.fgenv(telnet_addr, fg2client_addr, client2fg_addr)
    initial_state = myfgenv.initial()

    #假设
    print(initial_state)
    print("state dim", myfgenv.state_dim)
    #初始化dqn模型
    # mytfdqn = tfdqn.DQN(myfgenv.state_dim, 3)

    N_F = len(LLC_FEATURES)
    N_A = len(LLC_ACTIONS)
    myllc = LLC(N_F,N_A,LLC_ACTION_BOUNDS,LLC_GOALS)

    # if os.path.exists('modelckpt/model.ckpt'):
    # print("----------load model------------")
    # myllc.load(myllc.actor_sess,'modelckpt/llc_actor.ckpt')
    # myllc.load(myllc.critic_sess, 'modelckpt/llc_critic.ckpt')
    ## 开始自动飞行
    for i in range(epoch):

        # reset flightgear

        state = myfgenv.replay()
        time.sleep(2)
        for s in range(step):

            action = myllc.choose_action(state,LLC_GOALS)
            
            # print(action)
            action_frame = myllc.format_action(action)

            next_state, reward, done, _ = myfgenv.step(action_frame)

            if done:
               reward -=1

            r_, td =myllc.learn(state,LLC_GOALS,reward,action,next_state)

            print("--[action:", "%0.3f,%0.3f,%0.3f,%0.3f,%0.3f"%tuple(action.tolist()) ,"]--[r: %.3f||r_ :%.3f||td: %.3f]--" % (reward,r_,td))
            

            state = next_state
            # print(state)
            ##限制收发频率
            time.sleep(0.1)
            if done:
                break
        print("----------save model---------")
        myllc.save(myllc.actor_sess,'modelckpt/llc_actor.ckpt')
        myllc.save(myllc.critic_sess, 'modelckpt/llc_critic.ckpt')
        if i % 10 == 9:
            myfgenv.reset()


