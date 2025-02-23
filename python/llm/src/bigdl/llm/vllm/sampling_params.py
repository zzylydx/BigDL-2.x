#
# Copyright 2016 The BigDL Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Some parts of this file is adapted from
# https://github.com/vllm-project/vllm/blob/v0.2.1.post1/vllm/sampling_params.py
# which is licensed under Apache License 2.0
#
# Copyright 2023 The vLLM team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Sampling parameters for text generation."""
from enum import IntEnum
from functools import cached_property
from typing import List, Optional, Union
from bigdl.llm.utils.common import invalidInputError

_SAMPLING_EPS = 1e-5


class SamplingType(IntEnum):
    GREEDY = 0
    RANDOM = 1
    BEAM = 2


class SamplingParams:
    """Sampling parameters for text generation.

    Overall, we follow the sampling parameters from the OpenAI text completion
    API (https://platform.openai.com/docs/api-reference/completions/create).
    In addition, we support beam search, which is not supported by OpenAI.

    Args:
        n: Number of output sequences to return for the given prompt.
        best_of: Number of output sequences that are generated from the prompt.
            From these `best_of` sequences, the top `n` sequences are returned.
            `best_of` must be greater than or equal to `n`. This is treated as
            the beam width when `use_beam_search` is True. By default, `best_of`
            is set to `n`.
        presence_penalty: Float that penalizes new tokens based on whether they
            appear in the generated text so far. Values > 0 encourage the model
            to use new tokens, while values < 0 encourage the model to repeat
            tokens.
        frequency_penalty: Float that penalizes new tokens based on their
            frequency in the generated text so far. Values > 0 encourage the
            model to use new tokens, while values < 0 encourage the model to
            repeat tokens.
        temperature: Float that controls the randomness of the sampling. Lower
            values make the model more deterministic, while higher values make
            the model more random. Zero means greedy sampling.
        top_p: Float that controls the cumulative probability of the top tokens
            to consider. Must be in (0, 1]. Set to 1 to consider all tokens.
        top_k: Integer that controls the number of top tokens to consider. Set
            to -1 to consider all tokens.
        use_beam_search: Whether to use beam search instead of sampling.
        length_penalty: Float that penalizes sequences based on their length.
            Used in beam search.
        early_stopping: Controls the stopping condition for beam search. It
            accepts the following values: `True`, where the generation stops as
            soon as there are `best_of` complete candidates; `False`, where an
            heuristic is applied and the generation stops when is it very
            unlikely to find better candidates; `"never"`, where the beam search
            procedure only stops when there cannot be better candidates
            (canonical beam search algorithm).
        stop: List of strings that stop the generation when they are generated.
            The returned output will not contain the stop strings.
        stop_token_ids: List of tokens that stop the generation when they are
            generated. The returned output will contain the stop tokens unless
            the stop tokens are sepcial tokens.
        ignore_eos: Whether to ignore the EOS token and continue generating
            tokens after the EOS token is generated.
        max_tokens: Maximum number of tokens to generate per output sequence.
        logprobs: Number of log probabilities to return per output token.
        skip_special_tokens: Whether to skip special tokens in the output.
    """

    def __init__(
        self,
        n: int = 1,
        best_of: Optional[int] = None,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        temperature: float = 1.0,
        top_p: float = 1.0,
        top_k: int = -1,
        use_beam_search: bool = False,
        length_penalty: float = 1.0,
        early_stopping: Union[bool, str]=False,
        stop: Optional[Union[str, List[str]]]=None,
        stop_token_ids: Optional[List[int]] = None,
        ignore_eos: bool = False,
        max_tokens: int = 16,
        logprobs: Optional[int] = None,
        skip_special_tokens: bool = True,
    ) -> None:
        self.n = n
        self.best_of = best_of if best_of is not None else n
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.use_beam_search = use_beam_search
        self.length_penalty = length_penalty
        self.early_stopping = early_stopping
        if stop is None:
            self.stop = []
        elif isinstance(stop, str):
            self.stop = [stop]
        else:
            self.stop = list(stop)
        if stop_token_ids is None:
            self.stop_token_ids = []
        else:
            self.stop_token_ids = list(stop_token_ids)
        self.ignore_eos = ignore_eos
        self.max_tokens = max_tokens
        self.logprobs = logprobs
        self.skip_special_tokens = skip_special_tokens

        self._verify_args()
        if self.use_beam_search:
            self._verify_beam_search()
        else:
            self._verify_non_beam_search()
            if self.temperature < _SAMPLING_EPS:
                # Zero temperature means greedy sampling.
                self._verify_greedy_sampling()

    def _verify_args(self) -> None:
        if self.n < 1:
            invalidInputError(f"n must be at least 1, got {self.n}.")
        if self.best_of < self.n:
            invalidInputError(f"best_of must be greater than or equal to n, "
                              f"got n={self.n} and best_of={self.best_of}.")
        if not -2.0 <= self.presence_penalty <= 2.0:
            invalidInputError("presence_penalty must be in [-2, 2], got "
                              f"{self.presence_penalty}.")
        if not -2.0 <= self.frequency_penalty <= 2.0:
            invalidInputError("frequency_penalty must be in [-2, 2], got "
                              f"{self.frequency_penalty}.")
        if self.temperature < 0.0:
            invalidInputError(
                f"temperature must be non-negative, got {self.temperature}.")
        if not 0.0 < self.top_p <= 1.0:
            invalidInputError(f"top_p must be in (0, 1], got {self.top_p}.")
        if self.top_k < -1 or self.top_k == 0:
            invalidInputError(f"top_k must be -1 (disable), or at least 1, "
                              f"got {self.top_k}.")
        if self.max_tokens < 1:
            invalidInputError(
                f"max_tokens must be at least 1, got {self.max_tokens}.")
        if self.logprobs is not None and self.logprobs < 0:
            invalidInputError(
                f"logprobs must be non-negative, got {self.logprobs}.")

    def _verify_beam_search(self) -> None:
        if self.best_of == 1:
            invalidInputError("best_of must be greater than 1 when using beam "
                              f"search. Got {self.best_of}.")
        if self.temperature > _SAMPLING_EPS:
            invalidInputError("temperature must be 0 when using beam search.")
        if self.top_p < 1.0 - _SAMPLING_EPS:
            invalidInputError("top_p must be 1 when using beam search.")
        if self.top_k != -1:
            invalidInputError("top_k must be -1 when using beam search.")
        if self.early_stopping not in [True, False, "never"]:
            invalidInputError(
                f"early_stopping must be True, False, or 'never', "
                f"got {self.early_stopping}.")

    def _verify_non_beam_search(self) -> None:
        if self.early_stopping is not False:
            invalidInputError("early_stopping is not effective and must be "
                              "False when not using beam search.")
        if (self.length_penalty < 1.0 - _SAMPLING_EPS
                or self.length_penalty > 1.0 + _SAMPLING_EPS):
            invalidInputError(
                "length_penalty is not effective and must be the "
                "default value of 1.0 when not using beam search.")

    def _verify_greedy_sampling(self) -> None:
        if self.best_of > 1:
            invalidInputError("best_of must be 1 when using greedy sampling."
                              f"Got {self.best_of}.")
        if self.top_p < 1.0 - _SAMPLING_EPS:
            invalidInputError("top_p must be 1 when using greedy sampling.")
        if self.top_k != -1:
            invalidInputError("top_k must be -1 when using greedy sampling.")

    @cached_property
    def sampling_type(self) -> SamplingType:
        if self.use_beam_search:
            return SamplingType.BEAM
        if self.temperature < _SAMPLING_EPS:
            return SamplingType.GREEDY
        return SamplingType.RANDOM

    def __repr__(self) -> str:
        return (f"SamplingParams(n={self.n}, "
                f"best_of={self.best_of}, "
                f"presence_penalty={self.presence_penalty}, "
                f"frequency_penalty={self.frequency_penalty}, "
                f"temperature={self.temperature}, "
                f"top_p={self.top_p}, "
                f"top_k={self.top_k}, "
                f"use_beam_search={self.use_beam_search}, "
                f"length_penalty={self.length_penalty}, "
                f"early_stopping={self.early_stopping}, "
                f"stop={self.stop}, "
                f"ignore_eos={self.ignore_eos}, "
                f"max_tokens={self.max_tokens}, "
                f"logprobs={self.logprobs}, "
                f"skip_special_tokens={self.skip_special_tokens})")
