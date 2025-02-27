import pandas as pd
import re

# TODO: a fileList.tab-ból (https://github.com/inutano/chip-atlas/wiki#tables-summarizing-metadata-and-files)
# először kiszűrni a sejtvonalakat, és utána csak azokat felhasználni ebben a kódban

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


metadata_path = '../data/raw/metadata/mouse_only_tf.tsv'
data = read_data(metadata_path)
cell_lines_brenda = '../data/raw/cell_lines/cell_lines_brenda.txt'
cell_lines_mm10 = '../data/raw/cell_lines/mm10_added_cell_lines.txt'
other_keywords = '../data/raw/cell_lines/keywords.txt'
cellosaurus_mm10 = '../data/raw/cell_lines/cellosaurus_mouse.tsv'

# Kulcszavak
filter_out_track_type = ['Epitope tags', 'GFP']
filter_out_cell_type_class = ['Placenta', 'Embryo', 'Pluripotent stem cell', 'No description', 'Embryonic fibroblast']
filter_out_cell_type = read_keywords(cell_lines_brenda, other_keywords, cellosaurus_mm10)

# Először a track type oszlop alapján szűrűnk, mert az a legeffektívebb.
# Cell type utoljára, mert ott van a legtöbb kulcsszó. Ez hosszabb ideig is futhat
print("filtering track type column...")
data, removed_track_type = filter_data(data, 1, filter_out_track_type)
print("filtering cell type class column...")
data, removed_cell_type_class = filter_data(data, 2, filter_out_cell_type_class)
print("filtering cell type column...")
data, removed_cell_type = filter_data(data, 3, filter_out_cell_type)

# Törölt adatok mentése
removed_lines = pd.concat([removed_cell_type_class, removed_track_type, removed_cell_type],ignore_index=True)
removed_lines.to_csv('../data/processed/metadata/human_removed_keywords.tsv', index=False, sep='\t')

# Megtartott adatok mentése
data.to_csv('../data/processed/metadata/human_cleaned_keywords.tsv', index=False, sep='\t')