import ass
from pydub import AudioSegment
import os
from pathlib import Path
import re
from num2words import num2words
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import csv
import unittest

class ASSFileOrganizer:
    total_duration = 0
    export_one = True
    is_xml = False
    files_path = 'C:\\Projects\\python\\assorganizer\\files'
    export_path = 'C:\\Projects\\python\\assorganizer\\processed'

    def process_file(self, file_name):
        if os.path.isfile(self.files_path + "/" + file_name + ".wav"):

            if self.export_one is False:
                if not os.path.exists(self.export_path + "/" + file_name):
                    os.makedirs(self.export_path + "/" + file_name)

            slices = []
            temp_arr = []
            song = AudioSegment.from_wav(self.files_path + "/" + file_name + ".wav")

            if not self.is_xml:
                with open(self.files_path + "/" + file_name + '.ass', encoding='utf_8_sig') as f:
                    doc = ass.parse(f)
                    for a in doc.events:
                        if self.sum_time_deltas(temp_arr) < 10:
                            temp_arr.append(a)
                        else:
                            slices.append({
                                'start': temp_arr[0].start,
                                'end': temp_arr[-1].end,
                                'text': ' '.join(map(lambda x: x.text.strip(), temp_arr))
                            })
                            temp_arr = []

                self.process_slices(slices, file_name, song)
            else:
                with open(self.files_path + "/" + file_name + '.xml', 'r', encoding='utf_8_sig') as xml_file:
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
                                                            token_time = timedelta(seconds=float(
                                                                child_child_child_child_elem.items()[0][1]))
                                                            token_length = timedelta(seconds=float(
                                                                child_child_child_child_elem.items()[1][1]))
                                                            token_text = child_child_child_child_elem.items()[2][1]

                                                            a = type('', (), {})()
                                                            a.start = token_time
                                                            a.end = token_time + token_length  # timedelta(seconds=float(parse_time_delta(token_time, 's') + parse_time_delta(token_length, 's')))
                                                            a.text = token_text

                                                            if self.sum_time_deltas(temp_arr) < 10:
                                                                temp_arr.append(a)
                                                            else:
                                                                slices.append({
                                                                    'start': temp_arr[0].start,
                                                                    'end': temp_arr[-1].end,
                                                                    'text': ' '.join(
                                                                        map(lambda x: x.text.strip(), temp_arr))
                                                                })

                                                                temp_arr = []
                if len(temp_arr) > 0:
                    slices.append({
                        'start': temp_arr[0].start,
                        'end': temp_arr[-1].end,
                        'text': ' '.join(map(lambda x: x.text.strip(), temp_arr))
                    })

                self.process_slices(slices, file_name, song)
        else:
            pass

    def process_slices(self, slices, file_name, song):
        for slice_obj in slices:
            export_file_name = str(file_name + "_" + str(slice_obj['start']) + "_" + str(slice_obj['end'])).replace('.',
                                                                                                                    '_').replace(
                ':', '_')
            if self.parse_time_delta(slice_obj['end'] - slice_obj['start'], 's') < 99999:

                if self.time_delta_to_ms(slice_obj['start']) != 0:
                    start_time = self.time_delta_to_ms(slice_obj['start']) - 70
                else:
                    start_time = self.time_delta_to_ms(slice_obj['start'])

                end_time = self.time_delta_to_ms(slice_obj['end']) + 70

                if self.export_one is True:
                    if os.path.isfile(self.export_path + "/" + export_file_name + ".wav") is False:
                        self.total_duration += end_time - start_time

                        song[start_time:end_time].export(self.export_path + "/" + export_file_name + ".wav", format="wav")

                        with open(self.export_path + "/" + 'result.txt', 'a') as f:
                            f.write(export_file_name + " " + self.process_slice_text(slice_obj['text']) + "\n")

                        with open(self.export_path + '/result.csv', 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([export_file_name, self.process_slice_text(slice_obj['text'])])
                else:
                    if os.path.isfile(self.export_path + "/" + file_name + "/" + export_file_name + ".wav") is False:
                        self.total_duration += end_time - start_time

                        song[start_time:end_time].export(self.export_path + "/" + file_name + "/" + export_file_name + ".wav", format="wav")

                        with open(self.export_path + "/" + file_name + "/" + file_name + '.txt', 'a') as f:
                            f.write(export_file_name + " " + self.process_slice_text(slice_obj['text']) + "\n")

    def process_slice_text(self, text):
        # remove between brackets
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

        # made upper case
        text = self.safe_upper(text)

        # custom rules
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
        text = text.replace('Þ', 'Ş')
        text = text.replace('Ð', 'Ğ')

        spacedArr = ['on', 'yirmi', 'otuz', 'kırk', 'elli', 'altmış', 'yetmiş', 'seksen', 'doksan', 'yüz', 'bin', 'bir',
                     'iki', 'üç', 'dört', 'beş', 'altı', 'yedi', 'sekiz', 'dokuz']

        found = re.findall('\d+', text)
        for f in found:
            if f.isnumeric():
                numtost = num2words(int(f), lang='tr')
                print(numtost)
                if numtost != None and numtost != '':
                    for spacedArrItem in spacedArr:
                        if spacedArrItem in numtost:
                            numtost = numtost.replace(spacedArrItem, spacedArrItem + ' ')
                numtost = self.safe_upper(numtost)
                print(numtost)
                text = text.replace(f, numtost + " ")

        # strip whitespaces
        text = self.safe_clear_whitespaces(text)

        return text

    def safe_clear_whitespaces(self, text):
        text = re.sub(' +', ' ', text)
        text = re.sub('/\s+', ' ', text)
        text = re.sub('^/\s', '', text)
        text = re.sub('/\s$', '', text)
        text = text.strip()
        return text

    def safe_upper(self, text):
        will = ['i', 'ğ', 'ı', 'ö', 'ş', 'ü', 'ç', 'ş']
        res = ['İ', 'Ğ', 'I', 'Ö', 'Ş', 'Ü', 'Ç', 'Ş']
        for char in text:
            if char in will:
                text = text.replace(char, res[will.index(char)])
        text = text.upper()
        return text

    def time_delta_to_ms(self, time_delta):
        ms = 0

        ms += self.parse_time_delta(time_delta, 'h') * 3600 * 1000
        ms += self.parse_time_delta(time_delta, 'm') * 60 * 1000
        ms += self.parse_time_delta(time_delta, 's') * 1000

        return ms

    def parse_time_delta(self, val, type):
        if type == 'h':
            return float(str(val).split(':')[0].split('.')[0])

        if type == 'm':
            return float(str(val).split(':')[1].split('.')[0])

        if type == 's':
            if ':' in str(val):
                return float(str(val).split(':')[2])
            else:
                return float(str(val))

    def sum_time_deltas(self, events):
        sum_result = 0

        for event in events:
            total_seconds = event.end - event.start
            sum_result += self.parse_time_delta(total_seconds, 's')

        return float(sum_result)

    def start_process(self):
        for child in Path(self.files_path).iterdir():
            if child.is_file():
                without_extension = str(os.path.splitext(child)[0]).split('\\')[-1]
                try:
                    self.process_file(without_extension)
                except Exception as e:
                    print(without_extension + ' ' + str(e))

        print("Total duration by minutes: " + str(self.total_duration / 1000 / 60))
