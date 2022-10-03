from __future__ import annotations  # For Python 3.7
from transformers import MarianMTModel, MarianTokenizer
from typing import Sequence
from dataclasses import dataclass
from typing import List
from bs4 import BeautifulSoup
import stanza
import translators as ts
from torch import cuda
import logging

## HTML stripping code for removing HTML code before the translation

def strip_tags(str):
    if bool(BeautifulSoup(str, "html.parser").find()):
        text = BeautifulSoup(str).get_text()
        return text
    else:
        return str


## Offline translation portion which uses Pytorch and Marian MT Transformer in order to translate Russian offline
## This section is largely adapted from the offline translator tutorial that can be found in the following link:
## https://skeptric.com/python-offline-translation/
stanza.download('ru')
nlp = stanza.Pipeline('ru', processors='tokenize')


@dataclass(frozen=True)
class SentenceBoundary:
    text: str
    prefix: str

    def __str__(self):
        return self.prefix + self.text


def minibatch(seq, size):
    items = []
    for x in seq:
        items.append(x)
        if len(items) >= size:
            yield items
            items = []
    if items:
        yield items


@dataclass(frozen=True)
class SentenceBoundaries:
    sentence_boundaries: List[SentenceBoundary]

    @classmethod
    def from_doc(cls, doc: stanza.Document) -> SentenceBoundaries:
        sentence_boundaries = []
        start_idx = 0
        for sent in doc.sentences:
            sentence_boundaries.append(
                SentenceBoundary(text=sent.text, prefix=doc.text[start_idx:sent.tokens[0].start_char]))
            start_idx = sent.tokens[-1].end_char
        sentence_boundaries.append(SentenceBoundary(text='', prefix=doc.text[start_idx:]))
        return cls(sentence_boundaries)

    @property
    def nonempty_sentences(self) -> List[str]:
        return [item.text for item in self.sentence_boundaries if item.text]

    def map(self, d: dict[str, str]) -> SentenceBoundaries:
        return SentenceBoundaries([SentenceBoundary(text=d.get(sb.text, sb.text),
                                                    prefix=sb.prefix) for sb in self.sentence_boundaries])

    def __str__(self) -> str:
        return ''.join(map(str, self.sentence_boundaries))


class Translator:
    def __init__(self, source_lang: str, dest_lang: str, use_gpu: bool = False) -> None:
        self.use_gpu = use_gpu
        self.model_name = f'Helsinki-NLP/opus-mt-{source_lang}-{dest_lang}'
        self.model = MarianMTModel.from_pretrained(self.model_name)
        if use_gpu:
            self.model = self.model.cuda()
        self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
        self.sentencizer = stanza.Pipeline(source_lang, processors='tokenize', verbose=False, use_gpu=use_gpu)

    def sentencize(self, texts: Sequence[str]) -> List[SentenceBoundaries]:
        return [SentenceBoundaries.from_doc(self.sentencizer.process(text)) for text in texts]

    def translate(self, texts: Sequence[str], batch_size: int = 10, truncation=True) -> Sequence[str]:
        if isinstance(texts, str):
            raise ValueError('Expected a sequence of texts')
        text_sentences = self.sentencize(texts)
        translations = {sent: None for text in text_sentences for sent in text.nonempty_sentences}

        for text_batch in minibatch(sorted(translations, key=len, reverse=True), batch_size):
            tokens = self.tokenizer(text_batch, return_tensors="pt", padding=True, truncation=truncation)
            if self.use_gpu:
                tokens = {k: v.cuda() for k, v in tokens.items()}
            translate_tokens = self.model.generate(**tokens)
            translate_batch = [self.tokenizer.decode(t, skip_special_tokens=True) for t in translate_tokens]
            for (text, translated) in zip(text_batch, translate_batch):
                translations[text] = translated

        return [str(text.map(translations)) for text in text_sentences]


marian_ru_en = Translator('ru', 'en')
marian_ru_en.translate(['что слишком сознавать — это болезнь, настоящая, полная болезнь.'])

def online_translate(str):
    try:
        translation = ts.google(str)
        return translation
    except:
        try:
            logging.error('Google Translate API failed. Trying another API')
            translation = ts.sogou(str)
            return translation
        except:
            try:
                logging.error('Sogou Translate API failed. Trying another API')
                translation = ts.bing(str)
                return translation
            except:
                try:
                    logging.error('Bing Translate API failed. Trying another API')
                    translation = ts.deepl(str, from_language='ru',to_language='en')
                    return translation
                except:
                    logging.error('all preferred APIs have failed, returning None')
                    return None



def translate_email_bodies(pandas_df, local_translation = True):
    email_bodies = list(pandas_df['body'])
    email_bodies = list(map(strip_tags,email_bodies))
    if local_translation:
        marian_translator = Translator('ru', 'en', use_gpu=cuda.is_available())
        translations = marian_translator.translate(email_bodies)
        return translations
    else:
        translations = []
        for i in email_bodies:
            text = online_translate(i)
            translations.append(text)
        return translations

