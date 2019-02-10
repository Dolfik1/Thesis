import sys
import constants
from tensor2tensor.bin import t2t_datagen
from tensor2tensor.utils.metrics import METRICS_FNS

# ...

# METRICS_FNS['word_error_rate'] = word_error_rate

if __name__ == '__main__':
    argv = [
        #'--generate_data',
        '--problem', constants.PROBLEM_VALUE,
        '--data_dir=./data',
        '--tmp_dir=./data/tmp',
        '--t2t_usr_dir=./problems'

    ]
    sys.argv += argv

    t2t_datagen.main(None)