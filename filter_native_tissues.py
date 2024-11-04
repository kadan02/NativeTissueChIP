import pandas as pd
import csv
import re

rows = []
tsv_path = 'tsv/hg38_TF_filtered_experiments_relevant_columns.tsv'
with open(tsv_path, 'r', encoding='utf-8') as infile:
    for line in infile:
        # Split by tab and add to rows list
        rows.append(line.strip().split('\t'))

data = pd.DataFrame(rows)
data = data.replace('"', '', regex=True)

# Sejtvonalak neveit tartalmazó fájlok
cell_line_list_path = 'cell_lines/cell_line_list_all_no_duplicates.txt'
chip_atlas_cell_line_list_path = 'cell_lines/chip_atlas_added_cell_lines.txt'
other_keywords = 'cell_lines/keywords.txt'
with open(cell_line_list_path, 'r') as f:
    cell_lines = [line.strip() for line in f.readlines()]
with open(chip_atlas_cell_line_list_path, 'r') as f:
    chip_atlas_cell_lines = [line.strip() for line in f.readlines()]
with open(other_keywords, 'r') as f:
    other_keywords = [line.strip() for line in f.readlines()]

# Kiszűrendő kifejezések a 'Cell type class' (harmadik) oszlopban
filter_out_cell_type_class = ['Placenta', 'Gonad', 'Embryo', 'Pluripotent stem cell', 'No description']
# Kiszűrendő kifejezések a 'Cell type' (negyedik)  oszlopban
filter_out_cell_type = (cell_lines + chip_atlas_cell_lines + other_keywords)
# Kiszűrendő kifejezések a Track type (második) oszlopban
filter_out_track_type = ['Epitope tags', 'GFP']


# Teljes kulcsszavak/kifejezések megegyezése a táblázatban
escaped_filter_out_cell_type_class = [r'\b' + re.escape(term) + r'\b' for term in filter_out_cell_type_class]
escaped_filter_out_cell_type = [r'\b' + re.escape(term) + r'\b' for term in filter_out_cell_type]
escaped_filter_out_track_type = [r'\b' + re.escape(term) + r'\b' for term in filter_out_track_type]

# Kiszűrt sorok és a hozzájuk tartozó filter kulcsszó
removed_details = []

# Filterelés cell type class alapján
for keyword, escaped_keyword in zip(filter_out_cell_type_class, escaped_filter_out_cell_type_class):
    mask = data[2].astype(str).str.contains(escaped_keyword, case=False, na=False)

    removed_rows = data[mask].copy()
    removed_rows['Keyword'] = keyword
    removed_details.append(removed_rows)
    data = data[~mask]

# Filterelés cell type alapján
for keyword, escaped_keyword in zip(filter_out_cell_type, escaped_filter_out_cell_type):
    mask = data[3].astype(str).str.contains(escaped_keyword, case=False, na=False)

    removed_rows = data[mask].copy()
    removed_rows['Keyword'] = keyword
    removed_details.append(removed_rows)
    data = data[~mask]

# Filterelés track type alapján
for keyword, escaped_keyword in zip(filter_out_track_type, escaped_filter_out_track_type):
    mask = data[1].astype(str).str.contains(escaped_keyword, case=False, na=False)

    removed_rows = data[mask].copy()
    removed_rows['Keyword'] = keyword
    removed_details.append(removed_rows)
    data = data[~mask]

# Törölt sorok mentése
removed_data = pd.concat(removed_details, ignore_index=True)
removed_output_file = 'tsv/hg38_removed_experiments.tsv'
removed_data.to_csv(removed_output_file, index=False, sep='\t', escapechar='\\')

# Szűrésen átjutott adatok mentése
filtered_output_file = 'tsv/hg38_native_experiments.tsv'
data.to_csv(filtered_output_file, index=False, sep='\t', escapechar='\\')
