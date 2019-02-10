from __future__ import absolute_import
from __future__ import division

import os
from tensor2tensor.bin import t2t_trainer
from tensor2tensor.data_generators import problem as problem_lib
from tensor2tensor.data_generators import text_encoder
from tensor2tensor.utils import decoding
from tensor2tensor.utils import trainer_lib
from tensor2tensor.utils import usr_dir

from . import constants
import tensorflow as tf
import numpy as np

import six
from queue import *

flags = tf.flags
FLAGS = flags.FLAGS

def add_args(parser, local=False):
  arg = parser.add_argument

  dir_prefix = './'
  if not local:
    dir_prefix += 't2t/'

  arg('--data_dir', type=str, default=dir_prefix+'data',
    help='model directory to store source data (vocab)')
  arg('--output_dir', type=str, default=dir_prefix+'result',
    help='model directory to store checkpointed models')
  arg('--usr_dir', type=str, default=dir_prefix+'problems',
    help='directory with user problems')

def _create_hparams(args):
  hparams = trainer_lib.create_hparams(
    constants.HPARAMS_SET_VALUE,
    None, # FLAGS.hparams
    data_dir=os.path.expanduser(args.data_dir),
    problem_name=constants.PROBLEM_VALUE)
  hparams.sampling_method = "random"
  return hparams

def _save_until_eos(ids, skip=False):
  """Strips everything after the first <EOS> token, which is normally 1."""
  ids = ids.flatten()
  if skip:
    return ids
  try:
    index = list(ids).index(text_encoder.EOS_ID)
    return ids[0:index]
  except ValueError:
    # No EOS_ID: return the array as-is.
    return ids

def _create_decode_hparams(args):
  decode_hp = decoding.decode_hparams("")
  decode_hp.decode_to_file = False
  return decode_hp

class Chatbot():
  def __init__(self, args):
    usr_dir.import_usr_dir(args.usr_dir)
    self.hparams = _create_hparams(args)
    self.decode_hp = _create_decode_hparams(args)
    FLAGS.output_dir = args.output_dir
    self.queue = Queue()

  def start(self):
    self.running = True
    self.estimator = trainer_lib.create_estimator(
      constants.MODEL_VALUE,
      self.hparams,
      t2t_trainer.create_run_config(self.hparams),
      decode_hparams=self.decode_hp,
      use_tpu=False)
    
    self.num_samples = self.decode_hp.num_samples if self.decode_hp.num_samples > 0 else 1
    self.decode_length = self.decode_hp.extra_length
    p_hparams = self.hparams.problem_hparams
    self.has_input = "inputs" in p_hparams.modality
    self.vocabulary = p_hparams.vocabulary["inputs" if self.has_input else "targets"]
    # This should be longer than the longest input.
    self.const_array_size = 10000

    def input_fn():
      gen_fn = self._make_input_fn_from_generator(self._interactive_input_fn())
      example = gen_fn()
      example = self._interactive_input_tensor_to_features_dict(example)
      return example

    self.predict_iter = self.estimator.predict(input_fn)

  def stop(self):
    self.running = False

  def say(self, text):
    self.queue.put(text)
    result = next(self.predict_iter)
    targets_vocab = self.hparams.problem_hparams.vocabulary["targets"]
    output = targets_vocab.decode(_save_until_eos(
      result["outputs"], False))
    return output

  def _interactive_input_fn(self):
    """Generator that reads from the terminal and yields "interactive inputs".

    Due to temporary limitations in tf.learn, if we don't want to reload the
    whole graph, then we are stuck encoding all of the input as one fixed-size
    numpy array.

    We yield int32 arrays with shape [const_array_size].  The format is:
    [num_samples, decode_length, len(input ids), <input ids>, <padding>]

    Args:
      hparams: model hparams
      decode_hp: decode hparams
    Yields:
      numpy arrays

    Raises:
      Exception: when `input_type` is invalid.
    """
    decode_hp = self.decode_hp
    hparams = self.hparams

    num_samples = decode_hp.num_samples if decode_hp.num_samples > 0 else 1
    decode_length = decode_hp.extra_length
    input_type = "text"
    p_hparams = hparams.problem_hparams
    has_input = "inputs" in p_hparams.modality
    vocabulary = p_hparams.vocabulary["inputs" if has_input else "targets"]
    # This should be longer than the longest input.
    const_array_size = 10000
    while True:
      input_string = self.queue.get()
      input_ids = vocabulary.encode(input_string)

      if has_input:
        input_ids.append(text_encoder.EOS_ID)
      x = [num_samples, decode_length, len(input_ids)] + input_ids
      assert len(x) < const_array_size
      x += [0] * (const_array_size - len(x))
      features = {
          "inputs": np.array(x).astype(np.int32),
      }

      for k, v in six.iteritems(
          problem_lib.problem_hparams_to_features(p_hparams)):
        features[k] = np.array(v).astype(np.int32)
      yield features

  def _interactive_input_tensor_to_features_dict(self, feature_map):
    """Convert the interactive input format (see above) to a dictionary.

    Args:
      feature_map: dict with inputs.
      hparams: model hyperparameters

    Returns:
      a features dictionary, as expected by the decoder.
    """
    hparams = self.hparams
    inputs = tf.convert_to_tensor(feature_map["inputs"])

    x = inputs
    # Remove the batch dimension.
    num_samples = x[0]
    length = x[2]
    x = tf.slice(x, [3], tf.to_int32([length]))
    x = tf.reshape(x, [1, -1, 1, 1])
    # Transform into a batch of size num_samples to get that many random
    # decodes.
    x = tf.tile(x, tf.to_int32([num_samples, 1, 1, 1]))

    p_hparams = hparams.problem_hparams
    input_space_id = tf.constant(p_hparams.input_space_id)
    target_space_id = tf.constant(p_hparams.target_space_id)

    features = {}
    features["input_space_id"] = input_space_id
    features["target_space_id"] = target_space_id
    features["decode_length"] = (inputs[1])
    features["inputs"] = x
    return features

  def _make_input_fn_from_generator(self, gen):
    """Use py_func to yield elements from the given generator."""
    first_ex = six.next(gen)
    flattened = tf.contrib.framework.nest.flatten(first_ex)
    types = [t.dtype for t in flattened]
    shapes = [[None] * len(t.shape) for t in flattened]
    first_ex_list = [first_ex]

    def py_func():
      if first_ex_list:
        example = first_ex_list.pop()
      else:
        example = six.next(gen)
      return tf.contrib.framework.nest.flatten(example)

    def input_fn():
      flat_example = tf.py_func(py_func, [], types)
      _ = [t.set_shape(shape) for t, shape in zip(flat_example, shapes)]
      example = tf.contrib.framework.nest.pack_sequence_as(first_ex, flat_example)
      return example

    return input_fn