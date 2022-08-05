#!bin\bash
echo "start resample the audio"
IN_AUDIO=$1
OUT_AUDIO=$2
python wavtransfer.py \
	--in_dir "testaudios/${IN_AUDIO}" \
	--out_dir "resample_audios/${OUT_AUDIO}" \
	--input_sr 48000 \
	--dst_sr 16000 \
