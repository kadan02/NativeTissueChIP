import pandas as pd
import csv
import re


csv_path = 'chip_atlas/hg38_TF_all_experiments.csv'
data = pd.read_csv(csv_path, sep=',')
data.columns = data.columns.str.strip()
data = data.replace('"', '', regex=True)

# Sejtvonalak neveit tartalmazó fájlok
cell_line_list_path = 'cell_lines/homo_sapiens_cell_line.txt'
chip_atlas_cell_line_list_path = 'cell_lines/chip_atlas_added_cell_lines.txt'
with open(cell_line_list_path, 'r') as f:
    cell_lines = [line.strip() for line in f.readlines()]
with open(chip_atlas_cell_line_list_path, 'r') as f:
    chip_atlas_cell_lines = [line.strip() for line in f.readlines()]

# Kiszűrendő kifejezések a Cell type oszlopban
filter_out_cell_type = (['tumor', 'tumors', 'tumours', 'tumour', 'cancer', 'Sarcoma', 'Liposarcoma', 'Fibrosarcoma','leukemia',
               'adenocarcinoma','glioma', 'lymphoma', 'melanoma', 'Rhabdomyosarcoma', 'Polycystic', 'leiomyoma',
               'organoid', 'organoids', 'Unclassified', 'carcinoma', 'Neurofibromatosis', 'Aneurysm',
               'Fetal', 'Fetus', 'Embryo', 'Neural crest','hESC', 'hESCs', 'iPSC', 'iPS', 'xenograft', 'iTreg', 'iSLK',
               'Trophoblast stem cells'] + cell_lines + chip_atlas_cell_lines)

# Kiszűrendő kifejezések a Track type oszlopban
filter_out_track_type = ['Epitope tags', 'GFP']

# Kulcsszó kérdések: hESC, iPSC? (iPSC = szomatikus sejtből indukált pluripotens őssejt, pl egy májsejt volt az adatokban
# ilyen módon szekvenálva)
# Ötlet: esetleg külön katagória őssejteknek?

# Teljes kulcsszavak/kifejezések megegyezése a táblázatban
escaped_filter_out_cell_type = [r'\b' + re.escape(term) + r'\b' for term in filter_out_cell_type]
escaped_filter_out_track_type = [r'\b' + re.escape(term) + r'\b' for term in filter_out_track_type]

# Kiszűrt sorok és a hozzájuk tartozó filter kulcsszó
removed_details = []

# Filterelés sejttípus alapján
for keyword, escaped_keyword in zip(filter_out_cell_type, escaped_filter_out_cell_type):
    mask = data['Cell type'].astype(str).str.contains(escaped_keyword, case=False, na=False)

    # Ha kulcsszó match
    removed_rows = data[mask].copy()
    removed_rows['Keyword'] = keyword
    removed_details.append(removed_rows)
    data = data[~mask]

# Filterelés track type alapján
for keyword, escaped_keyword in zip(filter_out_track_type, escaped_filter_out_track_type):
    mask = data['Track type'].astype(str).str.contains(escaped_keyword, case=False, na=False)

    # Ha kulcsszó match
    removed_rows = data[mask].copy()
    removed_rows['Keyword'] = keyword
    removed_details.append(removed_rows)
    data = data[~mask]

# Törölt sorok mentése
removed_data = pd.concat(removed_details, ignore_index=True)
removed_output_file = 'chip_atlas/removed_chip_atlas_experiments_with_keyword.csv'
removed_data.to_csv(removed_output_file, index=False, sep=',', quoting=csv.QUOTE_NONE, escapechar='\\')

# Maradék adat mentése
filtered_output_file = 'chip_atlas/filtered_chip_atlas_experiments_no_cell_lines.csv'
data.to_csv(filtered_output_file, index=False, sep=',', quoting=csv.QUOTE_NONE, escapechar='\\')
