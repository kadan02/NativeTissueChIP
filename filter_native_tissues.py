import pandas as pd
import re

# TODO: rendes oszlop nevek?

# fájlbeolvasások
def read_data(tsv_path):
    rows = []
    with open(tsv_path, 'r', encoding='utf-8') as infile:
        for line in infile:
            rows.append(line.strip().split('\t'))
    data = pd.DataFrame(rows)
    data = data.replace('"', '', regex=True)  # lehet hogy redundáns? mindenesetre így működik.
    return data


def read_keywords(keyword_file_path):
    with open(keyword_file_path, 'r') as f:
        return [line.strip() for line in f.readlines()]


# kulcsszavak alapján filterelés
def filter_data(data, column_index, keywords):
    escaped_keywords = [r'\b' + re.escape(term) + r'\b' for term in keywords] # Teljes szavak megegyezése szűrésnél
    removed_details = [] # Kiszűrt sorok és a hozzájuk tartozó filter kulcsszó fog ide kerülni

    for keyword, escaped_keyword in zip(keywords, escaped_keywords):
        mask = data[column_index].astype(str).str.contains(escaped_keyword, case=False, na=False)
        removed_rows = data[mask].copy()
        removed_rows['Keyword'] = keyword
        removed_details.append(removed_rows)
        data = data[~mask]

    return data, removed_details


tsv_path = 'tsv/hg38_TF_filtered_experiments_relevant_columns.tsv'
data = read_data(tsv_path)
cell_lines_main = 'cell_lines/cell_line_list_all_no_duplicates.txt'
cell_lines_chipatlas = 'cell_lines/chip_atlas_added_cell_lines.txt'
other_keywords = 'cell_lines/keywords.txt'

# Kulcszavak
filter_out_cell_type_class = ['Placenta', 'Gonad', 'Embryo', 'Pluripotent stem cell', 'No description']
filter_out_cell_type = read_keywords(cell_lines_main) + read_keywords(cell_lines_chipatlas) + read_keywords(other_keywords)
filter_out_track_type = ['Epitope tags', 'GFP']

data, removed_cell_type_class = filter_data(data, 2, filter_out_cell_type_class)
data, removed_cell_type = filter_data(data, 3, filter_out_cell_type)
data, removed_track_type = filter_data(data, 1, filter_out_track_type)

# Törölt adatok mentése
removed_lines = pd.concat(removed_cell_type_class + removed_cell_type + removed_track_type, ignore_index=True)
removed_output_file = 'tsv/hg38_removed_experiments.tsv'
removed_lines.to_csv(removed_output_file, index=False, sep='\t', escapechar='\\')

# Megtartott adatok mentése
native_experiments_table = 'tsv/hg38_native_experiments.tsv'
data.to_csv(native_experiments_table, index=False, sep='\t', escapechar='\\')
