# MMML

import re
from typing import Literal

from ..utils.translation_literals import (
    ANSWER,
    CAUSE_LABELS,
    CONTRADICTION_LABELS,
    CORRECT_LABELS,
    EFFECT_LABELS,
    ENTAILMENT_LABELS,
    IMPOSSIBLE,
    INCORRECT_LABELS,
    LANGS,
    NEUTRAL_LABELS,
    NLI_QUESTION,
    NO_LABELS,
    QUESTION,
    YES_LABELS,
)
from lighteval.tasks.requests import Doc
from lighteval.tasks.tasks_prompt_formatting import LETTER_INDICES


# Notes:
# - For the context we can also put something in front (not implemented right now)

# QA-Tasks (multichoice)
MULTI_QA_TEMPLATE = "{context}{question_word}: {question}\n{answer_word}:"


def _get_multi_qa_prompt(lang: LANGS):
    def multi_qa_prompt(task_name: str, question: str, answers: list[str], gold_index, context: str | None = None):
        query = MULTI_QA_TEMPLATE.format(
            question=question,
            context=f"{context}\n" if context else "",
            question_word=QUESTION[lang],
            answer_word=ANSWER[lang],
        )
        return Doc(
            task_name=task_name,
            query=query,
            gold_index=gold_index,
            choices=[f" {c}" for c in answers if c],
            uncoditioned_prefix=f"{ANSWER[lang]}:",
        )

    return multi_qa_prompt


def get_mmlu_prompt(lang: LANGS):
    prompter = _get_multi_qa_prompt(lang)

    def adapter(line, task_name):
        return prompter(task_name, line["question"], line["choices"], LETTER_INDICES.index(line["answer"]))

    return adapter

def get_c3_prompt(lang: LANGS):
    prompter = _get_multi_qa_prompt(lang)
    return lambda line, task_name: prompter(task_name, line["question"], line["choice"], line["choice"].index(line["answer"]), context=line["context"])

def get_arc_prompt(lang: LANGS, nested_choices=False):
    prompter = _get_multi_qa_prompt(lang)

    def adapter(line, task_name):
        choices = line["choices"]["text"] if nested_choices else line["choices"]
        return prompter(task_name, line["question"], choices, LETTER_INDICES.index(line["answerKey"]))

    return adapter

def get_french_boolqa_prompt(lang: LANGS):
    prompter = _get_multi_qa_prompt(lang)

    def adapter(line, task_name):
        return prompter(
            task_name,
            line["question"],
            [ENTAILMENT_LABELS[lang], CONTRADICTION_LABELS[lang]],
            [1, 0].index(line["label"]),
            context=line["context"],
        )

    return adapter

def get_cmllu_prompt(lang: LANGS):
    prompter = _get_multi_qa_prompt(lang)
    return lambda line, task_name: prompter(
        task_name,
        line["Question"],
        [line["A"], line["B"], line["C"], line["D"]],
        LETTER_INDICES.index(line["Answer"])
    )
    
def get_thai_exams_prompt(lang: LANGS):
    prompter = _get_multi_qa_prompt(lang)
    def adapter(line, task_name):
        letters = [letter.lower() for letter in LETTER_INDICES[:5]]
        options = [line[letter] for letter in letters]
        non_empty_options = [opt for opt in options if opt != ""]
        gold_index = letters.index(line["answer"])
        return prompter(
            task_name,
            line["question"],
            non_empty_options,
            gold_index,
        )
    return adapter

def get_ceval_prompt(lang: LANGS):
    prompter = _get_multi_qa_prompt(lang)
    return lambda line, task_name: prompter(
        task_name,
        line["question"],
        [line["A"], line["B"], line["C"], line["D"]],
        LETTER_INDICES.index(line["answer"])
    )
    
def get_alghafa_prompt(lang: LANGS):
    prompter = _get_multi_qa_prompt(lang)
    def adapter(line, task_name):
        answer_index = int(line["label"])
        # Dynamically determining the choices by excluding '__few_shots', 'query' and 'label'
        choices_keys = [key for key in line.keys() if key not in ["query", "label", "__few_shots"]]
        choices = [line[key] for key in choices_keys]
        return prompter(task_name, line["query"], choices, answer_index)
    return adapter


def get_m_exams_prompt(lang: LANGS):
    prompter = _get_multi_qa_prompt(lang)

    def adapter(line, task_name):
        letters = line["question"]["choices"]["label"]
        texts = line["question"]["choices"]["text"]
        return prompter(
            task_name,
            line["question"]["stem"],
            texts,
            letters.index(line["label"]),
        )

    return adapter


def get_m_belebele_prompt(lang: LANGS):
    prompter = _get_multi_qa_prompt(lang)
    return lambda line, task_name: prompter(
        task_name,
        line["question"],
        [line[f"mc_answer{i}"] for i in range(1, 5)],
        int(line["correct_answer_num"]) - 1,
        line["flores_passage"],
    )


def get_m_xcsr_prompt(lang: LANGS):
    prompter = _get_multi_qa_prompt(lang)

    def adapter(line, task_name):
        letters = line["question"]["choices"]["label"]
        texts = line["question"]["choices"]["text"]
        return prompter(task_name, line["question"]["stem"], texts, letters.index(line["answerKey"]))

    return adapter

def get_agieval_prompt(lang: Literal["zh"]):
    prefix_re = re.compile(r"^\([A-D]\)")
    prompter = _get_multi_qa_prompt(lang)

    def adapter(line, task_name):
        # Remove the question at the start to get consistency
        # Ensure there is exactly one '问题：' in the query
        context, rest = line["query"].split("问题：", maxsplit=1)
        question, _ = rest.split(" 选项：", maxsplit=1)
        original_choices = line["choices"]
        no_letter_choices = [prefix_re.sub("", c) for c in original_choices]
        return prompter(task_name, question, no_letter_choices, line["gold"], context=context)
    return adapter


def get_m_m3exam_prompt(lang: LANGS):
    prompter = _get_multi_qa_prompt(lang)
    prefix_re = re.compile(r"^\([A-Da-d1-4]\)\s*|^[A-Da-d1-3]\.\s*")

    def adapter(line, task_name):
        is_letter_based = line["answer_text"].isalpha()
        clean_options = [prefix_re.sub("", c) for c in line["options"]]
        gold_idx = (
            LETTER_INDICES.index(line["answer_text"].upper()) if is_letter_based else int(line["answer_text"]) - 1
        )
        return prompter(task_name, line["question_text"], clean_options, gold_idx, context=line["background"])

    return adapter

def get_m_truthfulqa_prompt(lang: LANGS, type: Literal["mc1", "mc2"]):
    prompter = _get_multi_qa_prompt(lang)
    def adapter(line, task_name):

        choices = line[f"{type}_targets"]["choices"]
        labels = line[f"{type}_targets"]["labels"]
        gold_index = [ix for ix, label in enumerate(labels) if label == 1]
        return prompter(task_name, line["question"], choices, gold_index)
    return adapter


def get_sciq_prompt(lang: LANGS):
    prompter = _get_multi_qa_prompt(lang)
    return lambda line, task_name: prompter(task_name, line["question"], [line["distractor1"], line["distractor2"], line["distractor3"], line["correct_answer"]], 3, context=line["support"])


def get_acva_prompt(lang: LANGS):
    prompter = _get_multi_qa_prompt(lang)
    choices = [CORRECT_LABELS[lang], INCORRECT_LABELS[lang]]
    return lambda line, task_name: prompter(task_name, line["question"], choices, choices.index(line["answer"]))


# QA-Tasks (No multichoice)


QA_TEMPLATE = "{topic}{context}{question_word}: {question}\n{answer_word}:"
def _get_qa_prompt(lang: LANGS):
    def qa_prompt(
        task_name: str, question: str, answer: str, context: str | None = None, topic: str | None = None, instruction: str | None = None
    ):
        query = QA_TEMPLATE.format(
            topic=f"{topic}\n" if topic else "",
            question=question,
            context=f"{context}\n" if context else "",
            question_word=QUESTION[lang],
            answer_word=ANSWER[lang],
        )
        return Doc(
            task_name=task_name, instruction=instruction, query=query, gold_index=0, choices=[answer], uncoditioned_prefix=f"{ANSWER[lang]}:"
        )

    return qa_prompt


def get_mlqa_prompt(lang: LANGS):
    prompter = _get_qa_prompt(lang)
    return lambda line, task_name: prompter(task_name, line["question"], line["answers"]["text"], line["context"])


def get_mintaka_prompt(lang: LANGS):
    prompter = _get_qa_prompt(lang)
    return lambda line, task_name: prompter(task_name, line["question"], line["answerText"])

def get_cmath_prompt(lang: LANGS):
    prompter = _get_qa_prompt(lang)
    return lambda line, task_name: prompter(task_name, line["question"], line["golden"])


def get_french_fquadv2_prompt(lang):
    prompter = _get_qa_prompt(lang)
    # Possibly fix to allow multilang
    instruct = "après l'information dans le contexte donné, donne la réponse à la question en citant quelques mots du contexte. Si il est impossible de répondre avec les informations du contexte, répond 'Impossible."

    def adapter(task_name, line):
        answer = line["answers"]["text"][0] if line["answers"]["text"] else IMPOSSIBLE[lang]
        return prompter(task_name, line["question"], answer, context=line["context"], instruction=instruct)

    return adapter


# NLI premise/hypthesis
NLI_TEMPLATE = "{premise}, {question_word}? {label}, {hypothesis}"


def _get_nli_prompt(lang: LANGS, pos_labels: list[Literal["entailment", "neutral", "contradiction"]]):
    labels = []
    if "entailment" in pos_labels:
        labels.append(ENTAILMENT_LABELS[lang])
    if "neutral" in pos_labels:
        labels.append(NEUTRAL_LABELS[lang])
    if "contradiction" in pos_labels:
        labels.append(CONTRADICTION_LABELS[lang])

    def nli_prompt(task_name: str, premise: str, hypothesis: str, label: int):
        return Doc(
            task_name=task_name,
            query="",
            choices=[
                NLI_TEMPLATE.format(
                    premise=premise,
                    question_word=NLI_QUESTION[lang],
                    label=label,
                    hypothesis=hypothesis,
                )
                for label in labels
            ],
            gold_index=label,
            uncoditioned_prefix="",
        )

    return nli_prompt


def get_xnli_prompt(lang: LANGS):
    prompter = _get_nli_prompt(lang, ["entailment", "neutral", "contradiction"])
    return lambda line, task_name: prompter(task_name, line["premise"], line["hypothesis"], int(line["label"]))


def get_paws_x_prompt(lang: LANGS):
    prompter = _get_nli_prompt(lang, ["entailment", "contradiction"])
    return lambda line, task_name: prompter(task_name, line["sentence1"], line["sentence2"], int(line["label"]))

# NLI Cause/Effect (Copa)
COPA_TEMPLATE = "{premise} {cause_or_effect}"
def _get_copa_prompt(lang: LANGS):
    def copa_prompt(task_name: str, premise: str, cause_or_effect: Literal["cause", "effect"], hypotheses: list[str], gold_index: int):
        cause_effect_trans = CAUSE_LABELS[lang] if cause_or_effect == "cause" else EFFECT_LABELS[lang]
        return Doc(
            task_name=task_name,
            query="",
            choices=[
                COPA_TEMPLATE.format(
                    premise=premise,
                    cause_or_effect=cause_effect_trans,
                    hypothesis=f" {hypothesis}",
                )
                for hypothesis in hypotheses
            ],
            gold_index=gold_index,
            uncoditioned_prefix="",
        )

    return copa_prompt


def get_copa_prompt(lang: LANGS):
    # TODO: solve the punctuation issue
    prompter = _get_copa_prompt(lang)
    def adapter(line, task_name):
        premise = line["premise"].strip()[:-1]
        hyptheses = [f"{hyp[0].lower()}{hyp[1:]}" for hyp in [line["choice1"], line["choice2"]]]
        return prompter(task_name, premise, line["question"], hyptheses, int(line["label"]))
    return adapter




# QA YES/NO
def _get_boolq_prompt(lang: LANGS):
    yes, no = YES_LABELS[lang], NO_LABELS[lang]
    prompter = _get_multi_qa_prompt(lang)
    def boolq_prompt(task_name: str, question: str, label: bool, context: str | None = None):
        return prompter(task_name, question, [yes,no], 0 if label else 1, context)
    return boolq_prompt

def get_boolq_prompt(lang: LANGS):
    prompter = _get_boolq_prompt(lang)
    return lambda line, task_name: prompter(task_name, line["question"], line["answer"] == "true", context=line["passage"])

def get_indic_boolq_prompt(lang: LANGS):
    prompter = _get_boolq_prompt(lang)
    return lambda line, task_name: prompter(task_name, line["itv2 hi question"], line["answer"] == "true", context=line["itv2 hi passage"])


# NLI Hellaswag
DEFAULT_DOT_REPLACEMENT = [" [title]"]
DOT_REPLACEMENTS: dict[LANGS, list[str]] = {
# https://github.com/malhajar17/lm-evaluation-harness_turkish/blob/main/lm_eval/tasks/hellaswag_tr-v0.2/utils.py
    "tr": [" [title]"," [başlık]", " [adım]", " [header]"],
}

HELLASWAG_TEMPLATE = "{activity_label}{ctx}"
def _get_hellaswag_prompt(lang: LANGS):
    dot_replacment = DOT_REPLACEMENTS.get(lang, DEFAULT_DOT_REPLACEMENT)
    def preprocess(text):
        """Comes from AiHarness"""
        # text = text.strip()
        # NOTE: Brackets are artifacts of the WikiHow dataset portion of HellaSwag.
        for dot_repl in dot_replacment:
            text = text.replace(dot_repl, ". ")
        text = re.sub("\\[.*?\\]", "", text)
        text = text.replace("  ", " ")
        return text

    def hellaswag_prompt(task_name: str, ctx: tuple[str, str] | str, endings: list[str], label: int, activity_label: str | None = None):
        ctx = f"{ctx[0]} {ctx[1].capitalize()} " if isinstance(ctx, tuple) else ctx
        activity_label = f"{activity_label}: " if activity_label else ""
        full_context = HELLASWAG_TEMPLATE.format(activity_label=activity_label, ctx=ctx)
        return Doc(
            task_name=task_name,
            query=preprocess(full_context),
            choices=[" " + preprocess(ending) for ending in endings],
            gold_index=int(label) if label != "" else -1,  # -1 for test
            uncoditioned_prefix="",
    )
    return hellaswag_prompt

def get_hellaswag_prompt(lang: LANGS):
    prompter = _get_hellaswag_prompt(lang)
    return lambda line, task_name: prompter(task_name, (line["ctx_a"], line["ctx_b"]), line["endings"], line["label"], activity_label=line.get("activity_label"))


def get_hellaswag_prompt_full_ctx(lang: LANGS):
    prompter = _get_hellaswag_prompt(lang)
    return lambda line, task_name: prompter(task_name, line["ctx"], line["endings"], line["label"])

# NLI (collocations)

