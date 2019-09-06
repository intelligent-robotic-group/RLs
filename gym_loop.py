import numpy as np


def get_action_normalize_factor(space, action_type):
    '''
    input: {'low': [-2, -3], 'high': [2, 6]}, 'continuous'
    return: [0, 1.5], [2, 4.5]
    '''
    if action_type == 'continuous':
        return (space.high + space.low) / 2, (space.high - space.low) / 2
    else:
        return 0, 1


def maybe_one_hot(obs, obs_space):
    '''
    input: obs = 3, obs_space.n = 5
    return: [0, 0, 0, 1, 0, 0]
    '''
    if hasattr(obs_space, 'n'):
        return np.eye(obs_space.n)[obs]
    else:
        return obs


class Loop(object):

    @staticmethod
    def train(env, gym_model, action_type, begin_episode, save_frequency, max_step, max_episode, render, render_episode, train_mode):
        i = 1 if len(env.observation_space.shape) == 3 else 0
        mu, sigma = get_action_normalize_factor(env.action_space, action_type)
        state = [[[]], []]
        new_state = [[[]], []]
        for episode in range(begin_episode, max_episode):
            obs = env.reset()
            obs = maybe_one_hot(obs, env.observation_space)
            state[i] = np.array([obs])
            step = 0
            r = 0
            while True:
                step += 1
                if render or episode > render_episode:
                    env.render()
                action = gym_model.choose_action(s=state[0], visual_s=[state[1]])
                obs, reward, done, info = env.step(action[0] * sigma + mu)
                obs = maybe_one_hot(obs, env.observation_space)
                new_state[i] = np.array([obs])
                r += reward
                gym_model.store_data(
                    s=state[0],
                    visual_s=[state[1]],
                    a=action,
                    r=np.array([reward]),
                    s_=new_state[0],
                    visual_s_=[new_state[1]],
                    done=np.array([done])
                )
                state[i] = new_state[i]

                if train_mode == 'perStep':
                    gym_model.learn(episode)

                if done or step > max_step:
                    break

            if train_mode == 'perEpisode':
                gym_model.learn(episode)

            print(f'episode {episode} step {step}')
            gym_model.writer_summary(
                episode,
                total_reward=r,
                step=step
            )
            if episode % save_frequency == 0:
                gym_model.save_checkpoint(episode)

    @staticmethod
    def inference(env, gym_model, action_type):
        """
        inference mode. algorithm model will not be train, only used to show agents' behavior
        """
        i = 1 if len(env.observation_space.shape) == 3 else 0
        mu, sigma = get_action_normalize_factor(env.action_space, action_type)
        state = [[[]], []]
        while True:
            obs = env.reset()
            obs = maybe_one_hot(obs, env.observation_space)
            state[i] = np.array([obs])
            while True:
                action = gym_model.choose_action(s=state[0], visual_s=[state[1]])
                obs, reward, done, info = env.step(action[0] * sigma + mu)
                obs = maybe_one_hot(obs, env.observation_space)
                state[i] = np.array([obs])

    @staticmethod
    def no_op(env, gym_model, action_type, steps):
        assert type(steps) == int and steps > 0

        i = 1 if len(env.observation_space.shape) == 3 else 0
        state = [[[]], []]
        new_state = [[[]], []]

        obs = env.reset()
        obs = maybe_one_hot(obs, env.observation_space)
        state[i] = np.array([obs])

        if action_type == 'continuous':
            action = np.zeros(env.action_space.shape, dtype=np.int32)
        else:
            action = 0

        for step in range(steps):
            print(f'no op step {step}')
            obs, reward, done, info = env.step(action)
            obs = maybe_one_hot(obs, env.observation_space)
            new_state[i] = np.array([obs])
            gym_model.no_op_store(
                s=state[0],
                visual_s=[state[1]],
                a=np.array([action]),
                r=np.array([reward]),
                s_=new_state[0],
                visual_s_=[new_state[1]],
                done=np.array([done])
            )
            state[i] = new_state[i]
