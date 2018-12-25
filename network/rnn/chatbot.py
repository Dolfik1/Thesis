from __future__ import print_function

import numpy as np
import tensorflow as tf

import os
import pickle
import copy
import html

from model import Model


def add_args(parser):
    arg = parser.add_argument

    arg('--save_dir', type=str, default='models/reddit',
        help='model directory to store checkpointed models')
    arg('-n', type=int, default=500,
        help='number of characters to sample')
    arg('--prime', type=str, default=' ',
        help='prime text')
    arg('--beam_width', type=int, default=2,
        help='Width of the beam for beam search, default 2')
    arg('--temperature', type=float, default=1.0,
        help='sampling temperature'
        '(lower is more conservative, default is 1.0, which is neutral)')
    arg('--topn', type=int, default=-1,
        help='at each step, choose from only this many most likely characters;'
        'set to <0 to disable top-n filtering.')
    arg('--relevance', type=float, default=-1.,
        help='amount of "relevance masking/MMI (disabled by default):"'
        'higher is more pressure, 0.4 is probably as high as it can go without'
        'noticeably degrading coherence;'
        'set to <0 to disable relevance masking')


def get_paths(input_path):
    if os.path.isfile(input_path):
        # Passed a model rather than a checkpoint directory
        model_path = input_path
        save_dir = os.path.dirname(model_path)
    elif os.path.exists(input_path):
        # Passed a checkpoint directory
        save_dir = input_path
        checkpoint = tf.train.get_checkpoint_state(save_dir)
        if checkpoint:
            model_path = checkpoint.model_checkpoint_path
        else:
            raise ValueError('Checkpoint not found in {}.'.format(save_dir))
    else:
        raise ValueError('save_dir is not a valid path.')

    config_path = os.path.join(save_dir, 'config.pkl')
    vocab_path = os.path.join(save_dir, 'chars_vocab.pkl')
    return model_path, config_path, vocab_path


def initial_state(net, sess):
    # Return freshly initialized model states.
    return sess.run(net.zero_state)


def forward_text(net, sess, states, relevance, vocab, prime_text=None):
    if prime_text is not None:
        for char in prime_text:
            if relevance > 0.:
                # Automatically forward the primary net.
                _, states[0] = net.forward_model(sess, states[0], vocab[char])
                # If the token is newline, reset the mask net state;
                # else, forward it.
                if vocab[char] == '\n':
                    states[1] = initial_state(net, sess)
                else:
                    _, states[1] = net.forward_model(
                        sess, states[1], vocab[char])
            else:
                _, states = net.forward_model(sess, states, vocab[char])
    return states


# Strip out characters that are not part of the net's vocab.
def sanitize_text(vocab, text):
    return ''.join(i for i in text if i in vocab)


def initial_state_with_relevance_masking(net, sess, relevance):
    if relevance <= 0.:
        return initial_state(net, sess)
    else:
        return [initial_state(net, sess), initial_state(net, sess)]


def possibly_escaped_char(raw_chars):
    if raw_chars[-1] == ';':
        for i, c in enumerate(reversed(raw_chars[:-1])):
            if c == ';' or i > 8:
                return raw_chars[-1]
            elif c == '&':
                escape_seq = "".join(raw_chars[-(i + 2):])
                new_seq = html.unescape(escape_seq)
                backspace_seq = "".join(['\b'] * (len(escape_seq) - 1))
                diff_length = len(escape_seq) - len(new_seq) - 1
                return (backspace_seq +
                        new_seq +
                        "".join([' '] * diff_length) +
                        "".join(['\b'] * diff_length))
    return raw_chars[-1]


def consensus_length(beam_outputs, early_term_token):
    for l in range(len(beam_outputs[0])):
        if l > 0 and beam_outputs[0][l - 1] == early_term_token:
            return l - 1, True
        for b in beam_outputs[1:]:
            if beam_outputs[0][l] != b[l]:
                return l, False
    return l, False


def scale_prediction(prediction, temperature):
    if (temperature == 1.0):
        return prediction  # Temperature 1.0 makes no change
    np.seterr(divide='ignore')
    scaled_prediction = np.log(prediction) / temperature
    scaled_prediction = scaled_prediction - \
        np.logaddexp.reduce(scaled_prediction)
    scaled_prediction = np.exp(scaled_prediction)
    np.seterr(divide='warn')
    return scaled_prediction


def forward_with_mask(sess, net, states, input_sample, forward_args):
    # forward_args is a dictionary containing arguments
    # for generating probabilities.
    relevance = forward_args['relevance']
    mask_reset_token = forward_args['mask_reset_token']
    forbidden_token = forward_args['forbidden_token']
    temperature = forward_args['temperature']
    topn = forward_args['topn']

    if relevance <= 0.:
        # No relevance masking.
        prob, states = net.forward_model(sess, states, input_sample)
    else:
        # states should be a 2-length list:
        # [primary net state, mask net state].
        if input_sample == mask_reset_token:
            # Reset the mask probs when reaching mask_reset_token (newline).
            states[1] = initial_state(net, sess)
        primary_prob, states[0] = net.forward_model(
            sess, states[0], input_sample)
        primary_prob /= sum(primary_prob)
        mask_prob, states[1] = net.forward_model(sess, states[1], input_sample)
        mask_prob /= sum(mask_prob)
        prob = np.exp(np.log(primary_prob) - relevance * np.log(mask_prob))
    # Mask out the forbidden token (">") to prevent
    # the bot from deciding the chat is over)
    prob[forbidden_token] = 0
    # Normalize probabilities so they sum to 1.
    prob = prob / sum(prob)
    # Apply temperature.
    prob = scale_prediction(prob, temperature)
    # Apply top-n filtering if enabled
    if topn > 0:
        prob[np.argsort(prob)[:-topn]] = 0
        prob = prob / sum(prob)
    return prob, states


def beam_search_generator(sess, net, initial_state, initial_sample,
                          early_term_token, beam_width,
                          forward_model_fn, forward_args):
    '''Run beam search! Yield consensus tokens sequentially, as a generator;
    return when reaching early_term_token (newline).

    Args:
        sess: tensorflow session reference
        net: tensorflow net graph
             (must be compatible with the forward_net function)
        initial_state: initial hidden state of the net
        initial_sample: single token (excluding any seed/priming material)
            to start the generation
        early_term_token: stop when the beam reaches consensus on this token
            (but do not return this token).
        beam_width: how many beams to track
        forward_model_fn: function to forward the model, must be of the form:
            probability_output, beam_state =
                forward_model_fn(sess, net, beam_state,
                    beam_sample, forward_args)
            (Note: probability_output has to be
              a valid probability distribution!)
        tot_steps: how many tokens to generate before stopping,
            unless already stopped via early_term_token.
    Returns: a generator to yield a sequence of beam-sampled tokens.'''
    # Store state, outputs and probabilities for up to args.beam_width beams.
    # Initialize with just the one starting entry;
    # it will branch to fill the beam
    # in the first step.
    beam_states = [initial_state]  # Stores the best activation states
    # Stores the best generated output sequences so far.
    beam_outputs = [[initial_sample]]
    # Stores the cumulative normalized probabilities of the beams so far.
    beam_probs = [1.]

    while True:
        # Keep a running list of the best beam branches for next step.
        # Don't actually copy any big data structures yet, just keep references
        # to existing beam state entries, and then clone them as necessary
        # at the end of the generation step.
        new_beam_indices = []
        new_beam_probs = []
        new_beam_samples = []

        # Iterate through the beam entries.
        for beam_index, beam_state in enumerate(beam_states):
            beam_prob = beam_probs[beam_index]
            beam_sample = beam_outputs[beam_index][-1]

            # Forward the model.
            prediction, beam_states[beam_index] = forward_model_fn(
                sess, net, beam_state, beam_sample, forward_args)

            # Sample best_tokens from the probability distribution.
            # Sample from the scaled probability
            # distribution beam_width choices
            # (but not more than the number of positive
            # probabilities in scaled_prediction).
            count = min(beam_width, sum(
                1 if p > 0. else 0 for p in prediction))
            best_tokens = np.random.choice(len(prediction), size=count,
                                           replace=False, p=prediction)
            for token in best_tokens:
                prob = prediction[token] * beam_prob
                if len(new_beam_indices) < beam_width:
                    # If we don't have enough new_beam_indices,
                    # we automatically qualify.
                    new_beam_indices.append(beam_index)
                    new_beam_probs.append(prob)
                    new_beam_samples.append(token)
                else:
                    # Sample a low-probability beam to possibly replace.
                    np_new_beam_probs = np.array(new_beam_probs)
                    inverse_probs = -np_new_beam_probs + \
                        max(np_new_beam_probs) + min(np_new_beam_probs)
                    inverse_probs = inverse_probs / sum(inverse_probs)
                    sampled_beam_index = np.random.choice(
                        beam_width, p=inverse_probs)
                    if new_beam_probs[sampled_beam_index] <= prob:
                        # Replace it.
                        new_beam_indices[sampled_beam_index] = beam_index
                        new_beam_probs[sampled_beam_index] = prob
                        new_beam_samples[sampled_beam_index] = token
        # Replace the old states with the new states,
        # first by referencing and then by copying.
        already_referenced = [False] * beam_width
        new_beam_states = []
        new_beam_outputs = []
        for i, new_index in enumerate(new_beam_indices):
            if already_referenced[new_index]:
                new_beam = copy.deepcopy(beam_states[new_index])
            else:
                new_beam = beam_states[new_index]
                already_referenced[new_index] = True
            new_beam_states.append(new_beam)
            new_beam_outputs.append(
                beam_outputs[new_index] + [new_beam_samples[i]])
        # Normalize the beam probabilities so they don't drop to zero
        beam_probs = new_beam_probs / sum(new_beam_probs)
        beam_states = new_beam_states
        beam_outputs = new_beam_outputs
        # Prune the agreed portions of the outputs
        # and yield the tokens on which the beam has reached consensus.
        l, early_term = consensus_length(beam_outputs, early_term_token)
        if l > 0:
            for token in beam_outputs[0][:l]:
                yield token
            beam_outputs = [output[l:] for output in beam_outputs]
        if early_term:
            return


class Chatbot:
    def __init__(self, save_dir, n, prime, beam_width,
                 temperature, topn, relevance):
        self.save_dir = save_dir
        self.n = n
        self.prime = prime
        self.beam_width = beam_width
        self.temperature = temperature
        self.topn = topn
        self.relevance = relevance

    def start(self):
        model_path, config_path, vocab_path = get_paths(self.save_dir)
        # Arguments passed to sample.py direct us to a saved model.
        # Load the separate arguments by which that model
        # was previously trained.
        # That's saved_args. Use those to load the model.
        with open(config_path, 'rb') as f:
            saved_args = pickle.load(f)
        # Separately load chars and vocab from the save directory.
        with open(vocab_path, 'rb') as f:
            self.chars, self.vocab = pickle.load(f)
        # Create the model from the saved arguments, in inference mode.
        print("Creating model...")
        saved_args.batch_size = self.beam_width
        self.net = Model(saved_args, True)
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        # Make tensorflow less verbose; filter out info (1+)
        # and warnings (2+) but not errors (3).
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        self.sess = tf.Session(config=config)
        tf.global_variables_initializer().run(session=self.sess)
        self.saver = tf.train.Saver(self.net.save_variables_list())
        # Restore the saved variables, replacing the initialized values.
        print("Restoring weights...")
        self.saver.restore(self.sess, model_path)
        self.states = initial_state_with_relevance_masking(
            self.net, self.sess, self.relevance)

    def stop(self, type, value, traceback):
        self.sess.close()

    def reset(self):
        self.states = initial_state_with_relevance_masking(
            self.net, self.sess, self.relevance)

    def set_config(self, relevance, temperature,
                   topn, beam_width):

        if relevance is not None:
            if self.relevance <= 0. and relevance > 0.:
                self.states = [self.states, copy.deepcopy(self.states)]
            elif self.relevance > 0. and relevance <= 0.:
                self.states = self.states[0]
            self.relevance = relevance

        if temperature is not None:
            self.temperature = temperature

        if topn is not None:
            self.topn = topn

        if beam_width is not None:
            self.beam_width = beam_width

    def say(self, input_text):
        sanitized_text = sanitize_text(self.vocab, "> " + input_text + "\n>")
        self.states = forward_text(
            self.net, self.sess, self.states,
            self.relevance, self.vocab, sanitized_text)

        computer_response_generator = beam_search_generator(
            sess=self.sess, net=self.net,
            initial_state=copy.deepcopy(self.states),
            initial_sample=self.vocab[' '],
            early_term_token=self.vocab['\n'],
            beam_width=self.beam_width,
            forward_model_fn=forward_with_mask,
            forward_args={
                'relevance': self.relevance,
                'mask_reset_token': self.vocab['\n'],
                'forbidden_token': self.vocab['>'],
                'temperature': self.temperature, 'topn': self.topn})

        out_chars = []
        for i, char_token in enumerate(computer_response_generator):
            out_chars.append(possibly_escaped_char(self.chars[char_token]))
            self.states = forward_text(
                self.net, self.sess, self.states,
                self.relevance, self.vocab,
                self.chars[char_token])

            if i >= self.n:
                    break

        text = sanitize_text(self.vocab, "\n> ")
        self.states = forward_text(self.net, self.sess, self.states,
                                   self.relevance, self.vocab, text)
        return ''.join(out_chars)
