import pandas as pd
import re


# fájlbeolvasások
def read_data(tsv_path):
    rows = []
    with open(tsv_path, 'r', encoding='utf-8') as infile:
        for line in infile:
            rows.append(line.strip().split('\t'))
    data = pd.DataFrame(rows)
    data = data.replace('"', '', regex=True)
    return data


def read_keywords(keyword_file_path):
    with open(keyword_file_path, 'r') as f:
        return [line.strip() for line in f.readlines()]


# kulcsszavak alapján filterelés
def filter_data(data, column_index, keywords):
    escaped_keywords = [r'\b' + re.escape(term) + r'\b' for term in keywords] # Teljes kifejezések megegyezése
    removed_details = [] # Kiszűrt sorok és a hozzájuk tartozó filter kulcsszavak ide fognak kerülni

    for keyword, escaped_keyword in zip(keywords, escaped_keywords):
        mask = data[column_index].astype(str).str.contains(escaped_keyword, case=False, na=False)
        removed_rows = data[mask].copy()
        removed_rows['Keyword'] = keyword
        removed_details.append(removed_rows)
        data = data[~mask]

    # Az összes eltávolított sor összevonása egy DataFrame-be
    if removed_details:
        removed_details = pd.concat(removed_details, ignore_index=True)
    else:
        removed_details = pd.DataFrame(columns=data.columns.tolist() + ['Keyword'])

    return data, removed_details

metadata_path = 'tsv/mm10_TF_filtered_experiments_relevant_columns.tsv'
data = read_data(metadata_path)
cell_lines_brenda = 'cell_lines/cell_lines_brenda.txt'
cell_lines_mm10 = 'cell_lines/mm10_added_cell_lines.txt'
other_keywords = 'cell_lines/keywords.txt'
cellosaurus_mm10 = 'cell_lines/cellosaurus_mouse.tsv'

# Kulcszavak
filter_out_cell_type_class = ['Placenta', 'Embryo', 'Pluripotent stem cell', 'No description', 'Embryonic fibroblast']
filter_out_cell_type = (read_keywords(cell_lines_brenda) + read_keywords(other_keywords)
                        + read_keywords(cellosaurus_mm10))
filter_out_track_type = ['Epitope tags', 'GFP']

data, removed_cell_type_class = filter_data(data, 2, filter_out_cell_type_class)
data, removed_cell_type = filter_data(data, 3, filter_out_cell_type)
data, removed_track_type = filter_data(data, 1, filter_out_track_type)

# Törölt adatok mentése
removed_lines = pd.concat([removed_cell_type_class, removed_track_type, removed_cell_type],
                          ignore_index=True)
removed_output_file = 'tsv/cellosaurus_test/mm10_removed_runs.tsv'
removed_lines.to_csv(removed_output_file, index=False, sep='\t', escapechar='\\')

# Megtartott adatok mentése
native_experiments_table = 'tsv/cellosaurus_test/mm10_native_runs.tsv'
data.to_csv(native_experiments_table, index=False, sep='\t', escapechar='\\')
