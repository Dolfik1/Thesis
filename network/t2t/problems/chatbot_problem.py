import re
import os

from tensor2tensor.data_generators import problem
from tensor2tensor.data_generators import text_problems
from tensor2tensor.utils import registry

@registry.register_problem
class ChatbotProblem(text_problems.Text2TextProblem):
  """Chatbot problem"""

  @property
  def approx_vocab_size(self):
    return 2**19 #2**20  # ~1kk

  @property
  def max_subtoken_length(self):
    return None

  @property
  def is_generate_per_split(self):
    # generate_data will shard the data into TRAIN and EVAL for us.
    return False

  @property
  def dataset_splits(self):
    """Splits of data to produce and number of output shards for each."""
    # 10% evaluation data
    return [{
        "split": problem.DatasetSplit.TRAIN,
        "shards": 1,
    }, {
        "split": problem.DatasetSplit.EVAL,
        "shards": 9,
    }]

  def generate_samples(self, data_dir, tmp_dir, dataset_split):
    del tmp_dir
    del dataset_split

    files = [f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))]


    for file in files:
      file = os.path.join(data_dir, file)
      print("Processing {}...".format(file))
      with open(file, encoding="utf8") as f:
        q = None
        a = None
        for line in f:
          line = line[2:]
          if q is None:
            q = line
          elif a is None:
            a = line
          else:
            yield {
              "inputs": q,
              "targets": a,
            }
            q = line
            a = None
