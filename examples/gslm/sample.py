# Copyright (c) Facebook, Inc. and its affiliates.

# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import random
from typing import Optional

from fairseq import utils
import numpy as np
import torch
import torchaudio

from textless.data.speech_encoder import SpeechEncoder
from textless.vocoders.tacotron2.vocoder import TacotronVocoder
from sampler import UnitLanguageModelSampler

log_format = "[%(asctime)s] [%(levelname)s]: %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)
logger = logging.getLogger(__name__)


class GslmPipeline:
    def __init__(self, args):
        logger.info("Initializing the GSLM pipeline.")
        self.device = torch.device("cuda")
        if args.seed is not None:
            random.seed(args.seed)
            np.random.seed(args.seed)
            utils.set_torch_seed(args.seed)

        self.temperature = args.temperature
        self.tokens_framerate = 0.02  # HuBERT framerate
        self.max_length = 1000
        self.trim_trailing_audio_frames = 200
        self.sampling_kwargs = {
            "temperature": self.temperature,
            "sampling": True,
            "beam": 1,
            "prefix_size": -1,
            "max_len_a": 0.0,
            "max_len_b": self.max_length,
        }
        logger.info("... Loading the language model")
        self.sampler = UnitLanguageModelSampler.from_pretrained(
            args.language_model_data_dir,
        )
        logger.info("=> Done!")
        logger.info("... Loading the encoder")

        self.speech_encoder = SpeechEncoder.by_name(
            dense_model_name="hubert-base-ls960",
            quantizer_model_name="kmeans",
            vocab_size=args.vocab_size,
            need_f0=False,
            deduplicate=True,
            f0_normalizer=None,
            f0_quantizer=None,
        ).cuda()

        logger.info("=> Done!")
        logger.info("... Loading the vocoder")
        self.resynthesizer = TacotronVocoder.by_name(
            dense_model_name="hubert-base-ls960",
            quantizer_model_name="kmeans",
            vocab_size=args.vocab_size,
        ).cuda()

        logger.info("=> Done!")
        logger.info("Pipeline initialized!")

    def __call__(self, raw_audio, sample_rate):

        # maybe_resample methode resample input audio to 16000khz
        raw_audio = self.speech_encoder.maybe_resample(raw_audio, sample_rate)

        sample = self.speech_encoder(raw_audio)
        units = sample["units"]
        duration = sample["durations"].sum().item()
        #prefix_duration : prompt duration
        prefix_duration = self.tokens_framerate * duration
        target_duration = self.tokens_framerate * (
            self.max_length - self.trim_trailing_audio_frames
        )
        #self.max_length = 1000 * 20ms = 20s ; self.trim_trailing_audio_frames = 200 * 20ms = 4s

        #Test random units with uLM
        units = torch.randint(100,[1,60]).squeeze(0)
        units = units.cuda()

        unit_str = " ".join(list(map(str, units.tolist())))
        sampled_unit_str = self.sampler.sample([unit_str], **self.sampling_kwargs)[0]

        audio = self.resynthesizer(sampled_unit_str)
        audio = audio[
            : int(
                self.resynthesizer.output_sample_rate
                * (prefix_duration + target_duration)
            )
        ]

        return audio

    @property
    def output_sample_rate(self) -> int:
        return self.resynthesizer.output_sample_rate


def main(args):
    pipeline = GslmPipeline(args)

    audio, sample_rate = torchaudio.load(args.input_file)

    print("audio:",audio)
    print("audio shape: ", audio.size())
    print("sample rate", sample_rate)

    # squeeze tensor [1, len] -> [52224, ], or maybe fusion different channels
    if audio.ndim == 2:
        audio = audio.mean(0)

    # clip audio with the only prompt length, 3s by default. (note word programme ~ 3s)
    if args.prompt_duration_sec:
        prompt = int(args.prompt_duration_sec * sample_rate)
        audio = audio[:prompt]

    # audio length 48000 now
    generated_audio = pipeline(audio, sample_rate)

    print("generated_audio:",generated_audio)
    print("generated_audio shape: ", generated_audio.size())
    torchaudio.save(
        args.output_file,
        generated_audio.cpu().unsqueeze(0),
        pipeline.output_sample_rate,
    )


def cli_main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-file",
        type=str,
        required=True,
        help="Input filepath",
    )
    parser.add_argument(
        "--language-model-data-dir",
        type=str,
        required=True,
        help="Path to language model dataset config path",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperature: should be above 0.0",
    )
    parser.add_argument(
        "--prompt-duration-sec",
        type=float,
        default=None,
        help="Cutting prompts to a maximum duration",
    )
    parser.add_argument(
        "--output-file", type=str, help="Path where generated metadata is saved"
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--vocab-size",
        type=int,
        choices=[50, 100, 200],
        default=100,
        help="Vocabulary size used",
    )

    args = parser.parse_args()

    main(args)


if __name__ == "__main__":
    cli_main()
