import sys
import constants
from tensor2tensor.bin import t2t_trainer
from tensor2tensor.utils.metrics import METRICS_FNS

# ...

# METRICS_FNS['word_error_rate'] = word_error_rate

if __name__ == '__main__':
    argv = [
        #'--generate_data',
        '--problem', constants.PROBLEM_VALUE,
        '--model', constants.MODEL_VALUE,
        '--hparams_set=' + constants.HPARAMS_SET_VALUE,
        '--data_dir=./data',
        '--output_dir=./result',
        '--t2t_usr_dir=./problems',
        '--train_steps=10000',
        '--eval_steps=100'

    ]
    sys.argv += argv

    t2t_trainer.main(None)