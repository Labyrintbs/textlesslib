'''
A quick file to transfer a .m4a(default by ios, sample rate 48kHZ) to .wav(16KHZ, demanded by textlesslib) 
origin: https://stackoverflow.com/questions/42809732/python-wave-module-cant-change-audio-sampling-rate-without-affecting-playback
'''
import librosa
import argparse
import soundfile as sf
'''
UPDATE
libroa when saving the output changes the datatype to 32bit float by default. 
Hence, to save the array, use soundwrite and specify the datatype while saving the audio

data, samplerate = soundfile.read('old.wav')
sf.write("Test4.wav", x, 22050, subtype='PCM_16')
'''
parser = argparse.ArgumentParser()
parser.add_argument("--in_dir", 
        type=str,
        help="input wave directory")
parser.add_argument("--out_dir", 
        type=str,
        help="output wave directory")
parser.add_argument("--dst_sr", 
        type=int,
        default=16000,
        help="output wave sample rate, default 16khz ")
parser.add_argument("--input_sr", 
        type=int,
        default=48000,
        help="input wave sample rate, default 48khz ")
parser.add_argument("--norm", 
        action="store_true",
        help="if output wave is normlized between -1 and 1")
args = parser.parse_args()
input_audio_file = args.in_dir #48KHz
output_audio_file = args.out_dir #16KHZ
input_sr = args.input_sr
dst_sr = args.dst_sr
flag = args.norm

#SAME PLAYBACK SPEED
x, sr = librosa.load(input_audio_file, input_sr)
y = librosa.resample(x, input_sr, dst_sr)
librosa.output.write_wav(output_audio_file, y, dst_sr, flag)
"""
#SLOW PLAYBACK SPEED
x, sr = librosa.load(audio_file, sr=48000)
librosa.output.write_wav("Test2.wav", x, sr=44100, norm=False)
"""
