#!bin/bash
echo 'run textless test'
python sample.py --language-model-data-dir /home/si/intern/fang_hongming/LM/hubert100_lm --input-file 1089-134686-0000.flac --output-file output_new.wav --prompt-duration-sec 3 --temperature 0.7 --vocab-size 100
