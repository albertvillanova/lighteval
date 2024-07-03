# MIT License

# Copyright (c) 2024 The HuggingFace Team

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Literal

from ..utils.prompts import get_m_m3exam_prompt
from ..utils.translation_literals import LANG_NAMES_INVERTED
from lighteval.metrics.metrics import Metrics
from lighteval.tasks.lighteval_task import LightevalTaskConfig


LANGS = Literal["zh", "ru", "fr", "en", "es", "de", "ja", "th", "sw"]


class M3ExamTask(LightevalTaskConfig):
    def __init__(self, lang: LANGS):
        super().__init__(
            name=f"m3exam-{lang}",
            suite=("custom",),
            prompt_function=get_m_m3exam_prompt(lang),
            hf_repo="chiayewken/m3exam",
            hf_subset=LANG_NAMES_INVERTED[lang],
            evaluation_splits=("test",),
            few_shots_split="dev",
            few_shots_select=None,
            generation_size=-1,
            metric=(Metrics.loglikelihood_acc_norm, Metrics.loglikelihood_acc, Metrics.loglikelihood_acc_norm_pmi),
        )
