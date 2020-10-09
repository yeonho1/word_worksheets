import os
import codecs
import random
from fpdf import FPDF
from word_forms.word_forms import get_word_forms as gwf
import itertools

class SentenceSyntaxError(Exception):
    pass

class UnexpectedInputError(Exception):
    pass

class UnprocessedError(Exception):
    pass

class SentenceLine:
    word = None
    sentence = None

    def __init__(self, word, sentence):
        self.word = word
        self.sentence = sentence

    def get_blanked(self):
        forms = gwf(self.word)
        result = [self.word] \
            + list(
                itertools.chain.from_iterable(forms.values())
            )
        words_in_sentence = [x for x in self.sentence.split(' ') if x != '']
        for stem in result:
            for i, e in enumerate(words_in_sentence):
                if stem in e.lower():
                    words_in_sentence[i] = e.lower().replace(stem, '__' * len(stem))
        words_in_sentence[0] = words_in_sentence[0][0].upper() + words_in_sentence[0][1:]
        return ' '.join(words_in_sentence)

    @classmethod
    def from_dict(cls, c):
        try:
            word = c['word']
            sentence = c['sentence']
            return cls(word, sentence)
        except KeyError:
            raise SentenceSyntaxError('Invalid JSON Syntax')

    @classmethod
    def from_text(cls, content):
        cs = content.split('\t')
        if len(cs) == 1:
            space_split = content.split(' ')
            cs = [space_split[0], ' '.join(space_split[1:])]
        elif len(cs) > 2:
            raise SentenceSyntaxError('More than 1 tab exists.')
        return cls(cs[0], cs[1])

class TxtFile:
    filepath = None
    basename = None

    def __init__(self, filepath):
        self.filepath = filepath
        self.basename = os.path.basename(filepath)

    def get_sentences(self):
        result = []
        f = codecs.open(self.filepath, 'r', encoding='utf-8')
        lines = f.readlines()
        for i, c in enumerate(lines, start=1):
            try:
                result.append(SentenceLine.fromt_text(c))
            except SentenceSyntaxError as e:
                print(f"{self.basename} 파일을 읽어들이는 도중 오류가 발생했습니다.")
                print(f'Line {i}: ', e)
        return result


class Worksheet:
    lines = []
    pdf = None
    font_name = None

    # WARNING
    # Variables under this line are static constants.
    # Please DO NOT CHANGE this value on the code.
    NARROW_WIDTH = 7
    WIDTH = 15
    PIPE = '|'

    def __init__(self, sentences=None, fontname="NanumGothic.ttf"):
        if sentences is None:
            sentences = []
        if any([type(x) != SentenceLine for x in sentences]):
            raise UnexpectedInputError('There is a element which is not a SentenceLine object.')
        self.lines = sentences
        self.font_name = fontname

    def split_sentence(self, sent):
        result = []
        limit = 30
        if len(sent) >= limit:
            words = sent.split(' ')
            while len(words) > 0:
                word_lengths = [len(w) for w in words]
                while sum(word_lengths) > limit:
                    word_lengths.pop()
                word_count = len(word_lengths)
                result.append(' '.join(words[:word_count]))
                words = words[word_count:]
        else:
            result = [sent]
        return result

    def process(self):
        pdf = FPDF()
        pdf.add_page()
        fname, ext = os.path.splitext(self.font_name)
        pdf.add_font(fname, fname=self.font_name, uni=True)
        pdf.set_font(fname, size=17)
        lines = self.lines[:]
        for s in lines:
            word = s.word
            sentence = s.get_blanked()
            pdf.cell(len(word), self.WIDTH, txt=word, ln=0)
            pdf.set_text_color(255, 0, 0)
            space_len = 40 - len(word)
            pdf.cell(space_len, self.WIDTH, txt='', ln=0)
            pdf.cell(1, self.WIDTH, txt=self.PIPE, ln=0)
            pdf.set_text_color(0,0,0)
            sent_split = self.split_sentence(sentence)
            if len(sent_split) > 1:
                for j, l in enumerate(sent_split, start=1):
                    if j == len(sent_split):
                        pdf.cell(40, self.NARROW_WIDTH, txt='', ln=0)
                        pdf.set_text_color(255, 0, 0)
                        pdf.cell(1, self.NARROW_WIDTH, txt=self.PIPE, ln=0)
                        pdf.set_text_color(0,0,0)
                        pdf.cell(3, self.NARROW_WIDTH, txt=' ' * 7 + l, ln=0)
                        pdf.ln()
                        #pdf.cell(0, 6, txt='', ln=0)
                        break
                    elif j == 1:
                        #pdf.cell(0, 6, txt='', ln=0)
                        #pdf.ln()
                        pdf.cell(3, self.NARROW_WIDTH, txt=' ' * 7 + l, ln=0)
                    else:
                        pdf.cell(40, self.NARROW_WIDTH, txt='', ln=0)
                        pdf.set_text_color(255, 0, 0)
                        pdf.cell(1, self.NARROW_WIDTH, txt=self.PIPE, ln=0)
                        pdf.set_text_color(0,0,0)
                        pdf.cell(3, self.NARROW_WIDTH, txt=' ' * 7 + l)
                    pdf.ln()
            else:
                pdf.cell(3, self.WIDTH, txt=' ' * 7 + sent_split[0], ln=0)
            pdf.ln()
        self.pdf = pdf

    @classmethod
    def from_txt(cls, filepath):
        return cls(TxtFile(filepath).get_sentences())

    def save(self, filepath):
        if self.pdf is None or type(self.pdf) != FPDF:
            raise UnprocessedError('You didn\'t processed the worksheet. Please call worksheet.process() first.')
        self.pdf.output(filepath)