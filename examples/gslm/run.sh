#!bin/bash
echo 'run textless test'
python sample.py \
	--language-model-data-dir /home/si/intern/fang_hongming/LM/hubert100_lm \
   	--input-file resample_audios/re_Vert.wav \
   	--output-file regeneration_audios/ge_Vert.wav \
	--prompt-duration-sec 3 \
	--temperature 0.7 \
	--vocab-size 100
