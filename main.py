import ass
from pydub import AudioSegment
import os
from pathlib import Path
import re
from num2words import num2words
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import xlsxwriter
import csv

total_duration = 0
export_one = True
is_ass = False

files_path = './files'
export_path = './processed'

with open(export_path + '/result.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["filename", "text"])

def process_file(file_name):
    if os.path.isfile(files_path + "/" + file_name + ".wav"):
        global total_duration

        if export_one is False:
            if not os.path.exists(export_path + "/" + file_name):
                os.makedirs(export_path + "/" + file_name)

        slices = []
        temp_arr = []
        song = AudioSegment.from_wav(files_path + "/" + file_name + ".wav")

        if is_ass == True:
            with open(files_path + "/" + file_name + '.ass', encoding='utf_8_sig') as f:
                doc = ass.parse(f)
                for a in doc.events:
                    if sum_time_deltas(temp_arr) < 10:
                        temp_arr.append(a)
                    else:
                        slices.append({
                            'start': temp_arr[0].start,
                            'end': temp_arr[-1].end,
                            'text': ' '.join(map(lambda x: x.text.strip(), temp_arr))
                        })
                        temp_arr = []

            process_slices(slices, file_name, song)
        else:
            with open(files_path + "/" + file_name + '.xml', 'r', encoding='utf_8_sig') as xml_file:
                xml_tree = ET.parse(xml_file)
                for tag_elem in xml_tree.getroot():
                    if tag_elem.tag == 'Episode':
                        for child_elem in tag_elem:
                            if child_elem.tag == 'Section':
                                for child_child_elem in child_elem:
                                    if child_child_elem.tag == 'Turn':
                                        for child_child_child_elem in child_child_elem:
                                            if child_child_child_elem.tag == 'Phrase':
                                                for child_child_child_child_elem in child_child_child_elem:
                                                    if child_child_child_child_elem.tag == 'Token':
                                                        token_time = timedelta(seconds=float(child_child_child_child_elem.items()[0][1]))
                                                        token_length = timedelta(seconds=float(child_child_child_child_elem.items()[1][1]))
                                                        token_text = child_child_child_child_elem.items()[2][1]

                                                        a = type('', (), {})()
                                                        a.start = token_time
                                                        a.end = token_time + token_length #timedelta(seconds=float(parse_time_delta(token_time, 's') + parse_time_delta(token_length, 's')))
                                                        a.text = token_text

                                                        if sum_time_deltas(temp_arr) < 10:
                                                            temp_arr.append(a)
                                                        else:
                                                            slices.append({
                                                                'start': temp_arr[0].start,
                                                                'end': temp_arr[-1].end,
                                                                'text': ' '.join(map(lambda x: x.text.strip(), temp_arr))
                                                            })

                                                            temp_arr = []
            if(len(temp_arr) > 0):
                slices.append({
                    'start': temp_arr[0].start,
                    'end': temp_arr[-1].end,
                    'text': ' '.join(map(lambda x: x.text.strip(), temp_arr))
                })

            process_slices(slices, file_name, song)
    else:
        pass
        #print("File " + file_name + " not found.\n")


def process_slices(slices, file_name, song):
    global total_duration
    global row
    global worksheet

    for slice_obj in slices:
        export_file_name = str(file_name + "_" + str(slice_obj['start']) + "_" + str(slice_obj['end'])).replace('.', '_').replace(':', '_')
        if parse_time_delta(slice_obj['end'] - slice_obj['start'], 's') < 99999:
            if export_one is True:
                if os.path.isfile(export_path + "/" + export_file_name + ".wav") is False:
                    total_duration += time_delta_to_ms(slice_obj['end']) - time_delta_to_ms(slice_obj['start'])

                    song[time_delta_to_ms(slice_obj['start']):time_delta_to_ms(slice_obj['end'])].export(
                        export_path + "/" + export_file_name + ".wav", format="wav")

                    with open('./wrong.txt', 'a') as f:
                        for line in process_slice_text(slice_obj['text']).split():
                            regex = re.compile('[\[\]_!#$%^&*()<>?/|}{~]')
                            if regex.search(line) is not None:
                                print(process_slice_text(slice_obj['text']) + "\n")
                                f.write(line + '\n')

                    with open(export_path + "/" + 'result.txt', 'a') as f:
                        f.write(export_file_name + " " + process_slice_text(slice_obj['text']) + "\n")

                    with open(export_path + '/result.csv', 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([export_file_name, process_slice_text(slice_obj['text'])])
            else:
                if os.path.isfile(export_path + "/" + file_name + "/" + export_file_name + ".wav") is False:
                    total_duration += time_delta_to_ms(slice_obj['end']) - time_delta_to_ms(slice_obj['start'])

                    song[time_delta_to_ms(slice_obj['start']):time_delta_to_ms(slice_obj['end'])].export(
                        export_path + "/" + file_name + "/" + export_file_name + ".wav", format="wav")

                    #with open('./wrong.txt', 'a') as f:
                    #    for line in process_slice_text(slice_obj['text']).split():
                    #        regex = re.compile('[\[\]_!#$%^&*()<>?/|}{~]')
                    #        if regex.search(line) is not None:
                    #            print(process_slice_text(slice_obj['text']) + "\n")
                    #            f.write(line + '\n')

                    with open(export_path + "/" + file_name + "/" + file_name + '.txt', 'a') as f:
                        f.write(export_file_name + " " + process_slice_text(slice_obj['text']) + "\n")


def process_slice_text(text):
    #remove between brackets
    found = re.findall('(\[(.*?)\])', text)
    for f in found:
        text = text.replace(f[0], '')

    # change words with between <>
    found = re.findall('[a-zçöşğüıA-ZÇÖŞĞÜİ]+<[a-zçöşğüıA-ZÇÖŞĞÜİ ]+>', text)
    for f in found:
        right = f.split('<')[1].split('>')[0]
        text = text.replace(f, right)

    # change words with between {} (only alphabetic)
    found = re.findall('[a-zçöşğüıA-ZÇÖŞĞÜİ\-0-9]+\{[a-zçöşğüıA-ZÇÖŞĞÜİ\-0-9 ]+\}', text)
    for f in found:
        left = f.split('{')[0]
        right = f.split('{')[1].split('}')[0]
        if left.isnumeric():
            if '-' in right:
                right = ' '.join(right.split('-')) + " "
            text = text.replace(f, right)
        elif left == '%':
            text = text.replace(f, right)
        else:
            if '-' in right:
                right = ''.join(right.split('-')) + " "
                text = text.replace(f, right)
            else:
                text = text.replace(f, left)

    #made upper case
    text = safe_upper(text)

    #strip whitespaces
    text = safe_clear_whitespaces(text)

    #custom rules
    text = text.replace('%{YÜZDE}', 'YÜZDE ')
    text = text.replace('(?)', ' ')
    text = text.replace('.{NOKTA}', 'NOKTA ')
    text = text.replace('%', 'YÜZDE ')
    text = text.replace('TESEKA<T-S-K>', 'TSK ')
    text = text.replace('<ÖĞRENEBİLİCEZ>ÖĞRENEBİLECEĞİZ', 'ÖĞRENEBİLECEĞİZ ')
    text = text.replace('HDP{HEDEPE]', 'HDP ')
    text = text.replace('120{YÜZ', 'YÜZ YİRMİ ')
    text = text.replace('?', ' ')
    text = text.replace('C&A', 'CIA')
    text = text.replace('H&M', 'HEM')

    spacedArr = ['on', 'yirmi', 'otuz', 'kırk', 'elli', 'altmış', 'yetmiş', 'seksen', 'doksan', 'yüz', 'bin', 'bir', 'iki', 'üç', 'dört', 'beş', 'altı', 'yedi', 'sekiz', 'dokuz']

    found = re.findall('\d+', text)
    for f in found:
        if f.isnumeric():
            numtost = num2words(int(f), lang='tr')
            if numtost != None and numtost != '':
                for spacedArrItem in spacedArr:
                    if spacedArrItem in numtost:
                        numtost = numtost.replace(spacedArrItem, spacedArrItem + ' ')
            numtost = safe_upper(numtost)
            text = text.replace(f, numtost + " ")
    text = safe_clear_whitespaces(text)

    return text

def safe_clear_whitespaces(text):
    text = re.sub(' +', ' ', text)
    text = re.sub('/\s+',' ', text)
    text = re.sub('^/\s','', text)
    text = re.sub('/\s$','', text)
    text = text.strip()
    return text

def safe_upper(text):
    will = ['i', 'ğ', 'ı', 'ö', 'ş', 'ü', 'ç', 'ş']
    res = ['İ', 'Ğ', 'I', 'Ö', 'Ş', 'Ü', 'Ç', 'Ş']
    for char in text:
        if char in will:
            text = text.replace(char, res[will.index(char)])
    text = text.upper()
    return text

def time_delta_to_ms(time_delta):
    ms = 0

    ms += parse_time_delta(time_delta, 'h') * 3600 * 1000
    ms += parse_time_delta(time_delta, 'm') * 60 * 1000
    ms += parse_time_delta(time_delta, 's') * 1000

    return ms

def parse_time_delta(val, type):
    if type == 'h':
        return float(str(val).split(':')[0].split('.')[0])

    if type == 'm':
        return float(str(val).split(':')[1].split('.')[0])

    if type == 's':
        if ':' in str(val):
            return float(str(val).split(':')[2])
        else:
            return float(str(val))

def sum_time_deltas(events):
    sum_result = 0

    for event in events:
        total_seconds = event.end - event.start
        sum_result += parse_time_delta(total_seconds, 's')

    return float(sum_result)

for child in Path(files_path).iterdir():
    if child.is_file():
        without_extension = str(os.path.splitext(child)[0]).split('\\')[-1]
        try:
            process_file(without_extension)
        except Exception as e:
            print(without_extension + ' ' + str(e))

print("Total duration by minutes: " + str(total_duration / 1000 / 60))
