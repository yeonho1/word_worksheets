#-*-coding:utf-8-*-
print('필요한 모듈들을 불러오고 있습니다...')
import time
import_start = time.time()
import json
from random import shuffle
from fpdf import FPDF
from word_forms.word_forms import get_word_forms as gwf
import os
import codecs
print('모든 모듈을 불러왔습니다. (걸린 시간: %.3f초)' % (time.time() - import_start))

def get_space_len(word_length):
    return 40-word_length

def blank_stems(sentence, stems):
    # sentence = sentence.lower()
    words_in_sentence = [x for x in sentence.split(' ') if x != '']
    for stem in stems:
        for i, e in enumerate(words_in_sentence):
            if stem in e.lower():
                words_in_sentence[i] = e.lower().replace(stem, '__' * len(stem))
            # sentence = sentence.replace(stem, '__' * len(stem))
    words_in_sentence[0] = words_in_sentence[0][0].upper() + words_in_sentence[0][1:]
    return ' '.join(words_in_sentence)

def get_forms(word):
    forms = gwf(word)
    result = []
    for k in forms:
        for f in forms[k]:
            result.append(f)
    return result

def split(sent):
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

def convert(filepath):
    job_start = time.time()
    basename = os.path.basename(filepath)
    invalid_lines = []
    print(f'-----{basename} 파일의 처리를 시작합니다-----')
    filepath = os.path.abspath(filepath)
    f = codecs.open(filepath, 'r', encoding='utf-8')

    root = os.path.split(os.path.split(filepath)[0])[0]
    output_dir = os.path.join(root, 'output')
    if os.path.isfile(output_dir):
        print(f'파일 {output_dir}가 존재하기 때문에 변환할 수 없습니다!')
        return False
    elif not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    lines = list(enumerate(f.readlines(), start=1))
    shuffle(lines)
    lines = [(i, x.replace('\n', '')) for i, x in lines if x != '']

    stems = {}

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("NanumGothic", fname="NanumGothic.ttf", uni=True)
    pdf.set_font("NanumGothic", size=17)

    narrow_width = 7
    width = 15
    pipe = '｜'

    for i, line in lines:
        line_split = line.split('\t')
        line_split = [x.strip() for x in line_split if x.strip() != '']
        if len(line_split) > 2:
            invalid_lines.append((i, -1))
            print(line_split)
            continue
        if len(line_split) < 2:
            line_split = line.split(' ')
            line_split = [line_split[0], ' '.join(line_split[1:])]
            # invalid_lines.append((i, -2))
            # print(line_split)
            # continue
        word, sentence = tuple(line_split)
        word_length = len(word)
        if word in stems:
            s = stems[word]
        else:
            s = get_forms(word)
            s = sorted(s, reverse=True, key=lambda x: len(x))
            stems[word] = s

        blanked_sentence = blank_stems(sentence, s)
        pdf.cell(word_length, width, txt=word, ln=0)
        pdf.set_text_color(255, 0, 0)
        space_len = get_space_len(word_length)
        pdf.cell(space_len, width, txt='', ln=0)
        pdf.cell(1, width, txt=pipe, ln=0)
        pdf.set_text_color(0,0,0)
        sent_split = split(blanked_sentence)
        if len(sent_split) > 1:
            for j, l in enumerate(sent_split, start=1):
                if j == len(sent_split):
                    pdf.cell(40, narrow_width, txt='', ln=0)
                    pdf.set_text_color(255, 0, 0)
                    pdf.cell(1, narrow_width, txt=pipe, ln=0)
                    pdf.set_text_color(0,0,0)
                    pdf.cell(3, narrow_width, txt=' ' * 7 + l, ln=0)
                    pdf.ln()
                    #pdf.cell(0, 6, txt='', ln=0)
                    break
                elif j == 1:
                    #pdf.cell(0, 6, txt='', ln=0)
                    #pdf.ln()
                    pdf.cell(3, narrow_width, txt=' ' * 7 + l, ln=0)
                else:
                    pdf.cell(40, narrow_width, txt='', ln=0)
                    pdf.set_text_color(255, 0, 0)
                    pdf.cell(1, narrow_width, txt=pipe, ln=0)
                    pdf.set_text_color(0,0,0)
                    pdf.cell(3, narrow_width, txt=' ' * 7 + l)
                pdf.ln()
        else:
            pdf.cell(3, width, txt=' ' * 7 + sent_split[0], ln=0)
        pdf.ln()
    without_ext = os.path.splitext(basename)[0]
    output_file_path = os.path.join(output_dir, without_ext+'.pdf')
    pdf.output(output_file_path)
    for l, c in sorted(invalid_lines):
        if c == -1:
            print(f'{l}번째 줄이 잘못되었습니다. 탭이 1개보다 많습니다.')
        elif c == -2:
            print(f'{l}번쨰 줄이 잘못되었습니다. 탭이 존재하지 않습니다.')
        line_contents = lines[l-1][1].replace('\t','\\t').replace('\n','\\n')
        print(f'줄의 내용: [{line_contents}]')
    print(f'{basename} 파일의 처리가 완료되었습니다. (걸린 시간: {time.time() - job_start}초)')

if __name__ == '__main__':
    print('\'words\' 폴더 내의 있는 모든 파일을 변환 중입니다.')
    for root, dirs, files in os.walk('./words'):
        for filename in files:
            if filename.endswith('txt'):
                convert(os.path.join(root, filename))
    print('모든 파일이 변환되어 \'output\' 폴더에 저장되었습니다.')
