import pandas as pd
import re


# metaadatok beolvasása
def read_data(tsv_path):
    rows = []
    with open(tsv_path, 'r', encoding='utf-8') as infile:
        for line in infile:
            rows.append(line.strip().split('\t'))
    data = pd.DataFrame(rows)
    data = data.replace('"', '', regex=True)
    return data


# szűrendő kulcsszavak beolvasása
def read_keywords(*file_paths):
    keywords = []
    for path in file_paths:
        print("loading path: " + path)
        with open(path, 'r') as f:
            for line in f:
                keywords.append(line.strip())
    return keywords


def filter_data(data, column_index, keywords):
    """
    DataFrame sorait szűri a kulcsszavak alapján. Azokat a sorokat törli, ahol a "column_index" oszlop értéke megyezik
    az adott kulcsszóval. Külön visszaadja a megtartott és törölt soroknak megfelelő Dataframe-eket is.
    """
    keywords_regex = r'\b(?:' + '|'.join(map(re.escape, keywords)) + r')\b' # csak a teljes kifejezések matchelése
    mask = data[column_index].astype(str).str.contains(keywords_regex, case=False, na=False)
    removed_rows = data[mask].copy()
    data = data[~mask]

    # Extra oszlop a törölt sorokat tartalmazó Dataframe-be, ami a kulcsszavat rögzíti, ami alapján törlésre került
    removed_rows['Keyword'] = removed_rows[column_index]

    return data, removed_rows

# file útvonalak megadása
metadata_path = 'tsv/mm10_TF_filtered_experiments_relevant_columns.tsv'
data = read_data(metadata_path)
cell_lines_brenda = 'cell_lines/cell_lines_brenda.txt'
cell_lines_mm10 = 'cell_lines/mm10_added_cell_lines.txt'
other_keywords = 'cell_lines/keywords.txt'
cellosaurus_mm10 = 'cell_lines/cellosaurus_mouse.tsv'

# Kulcszavak "betöltése"
filter_out_track_type = ['Epitope tags', 'GFP']
filter_out_cell_type_class = ['Placenta', 'Embryo', 'Pluripotent stem cell', 'No description', 'Embryonic fibroblast']
filter_out_cell_type = read_keywords(cell_lines_brenda, other_keywords, cellosaurus_mm10)

# A szűrés függvény hívása. Először a track type oszlop alapján szűrűnk, mert az a legeffektívebb.
# Cell type utoljára, mert ott van a legtöbb kulcsszó. Ez hosszabb ideig is futhat.
print("filtering track type column...")
data, removed_track_type = filter_data(data, 1, filter_out_track_type)
print("filtering cell type class column...")
data, removed_cell_type_class = filter_data(data, 2, filter_out_cell_type_class)
print("filtering cell type column...")
data, removed_cell_type = filter_data(data, 3, filter_out_cell_type)

# Törölt adatok mentése
removed_lines = pd.concat([removed_cell_type_class, removed_track_type, removed_cell_type],ignore_index=True)
removed_lines.to_csv('tsv/cellosaurus_test/TEST_mm10_removed_runs.tsv', index=False, sep='\t')

# Megtartott adatok mentése
data.to_csv('tsv/cellosaurus_test/TEST_mm10_native_runs.tsv', index=False, sep='\t')