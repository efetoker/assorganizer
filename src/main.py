from pathlib import Path
from services.assfileorganizer import *

organizer = ASSFileOrganizer(False, "ass", './files', './processed', True, True)

for child in Path('./files').iterdir():
    if child.is_file():
        without_extension = str(os.path.splitext(child)[0]).split('\\')[-1]
        try:
            organizer.process_file(without_extension)
        except Exception as e:
            print(without_extension + ' ' + str(e))

print("Total duration by minutes: " + str(organizer.total_duration / 1000 / 60))

# with open('./wrong.txt', 'a') as f:
#    for line in process_slice_text(slice_obj['text']).split():
#        regex = re.compile('[\[\]_!#$%^&*()<>?/|}{~]')
#        if regex.search(line) is not None:
#            print(process_slice_text(slice_obj['text']) + "\n")
#            f.write(line + '\n')
