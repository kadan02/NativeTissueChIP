import pandas as pd
import re


def filter_experiment_list(input_path, genome_type, track_type='TFs and others'):
    """
    input_path: ExperimentList.tab útvonala (ami az összes experiment metaadatait tartalmazza a Chip-Atlas adatbázisban)
    genome_type: Az adott faj genom assembly-jének neve (pl. hg38, mm10)
    track type: pl. 'TFs and others', 'Input control', 'Histone', 'ATAC-seq', lásd: https://chip-atlas.org/peak_browser
    """
    rows = []
    with open(input_path, 'r', encoding='utf-8') as infile:
        for line in infile:
            rows.append(line.strip().split('\t'))
    df = pd.DataFrame(rows)
    df_filtered = df[(df[1] == genome_type) & (df[2] == track_type)].copy()
    df_filtered.drop(columns=[1, 2], inplace=True)
    return df_filtered


def read_keywords(*file_paths):
    """
    Beolvassa tetszőleges számú fájlból a kulcsszavakat egy halmazba.
    A fájlokban soronként egy kifejezésnek kell lennie.
    """
    keywords = set()
    for path in file_paths:
        print("loading path: " + path)
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                keywords.add(line.strip())
    return keywords


def filter_data(data, column_index, keywords):
    """
    DataFrame sorait szűri a kulcsszavak alapján. Azokat a sorokat törli, ahol az adott oszlop értéke megyezik
    az adott kulcsszóval.

    data (df): az adatokat tartalmazó DataFrame
    column_index (int): adott oszlop, amire szűrűnk
    keywords (list): Stringekből álló list, amiket szűrünk az adott oszlopban

    Return: Megtartott és Törölt soroknak megfelelő Dataframe-ek
    """

    # Reguláris expresszió a csak a teljes szavak match-elésére
    keywords_regex = r'\b(?:' + '|'.join(map(re.escape, keywords)) + r')\b'
    mask = data[column_index].astype(str).str.contains(keywords_regex, case=False, na=False)
    removed_rows = data[mask].copy()
    data = data[~mask]

    # Extra oszlop a törölt sorokat tartalmazó Dataframe-be, ami a kulcsszavat rögzíti, ami alapján törlésre került
    removed_rows['Keyword'] = removed_rows[column_index]

    return data, removed_rows


if __name__ == "__main__":

    # 1. ExperimentList.tab filterelése, DataFrame létrehozása
    experiment_list_path = '../data/raw/metadata/experimentList.tab'
    filtered_df = filter_experiment_list(experiment_list_path, 'hg38')

    # 2. Kulcsszavak betöltése. Egyelőre itt manuálisan kell megadni a fájlokat a cell lines mappából
    keyword_files = [
        '../data/raw/cell_lines/cellosaurus_human.tsv',
        '../data/raw/cell_lines/hg38_added_cell_lines.txt',
        '../data/raw/cell_lines/cell_lines_brenda.txt',
        '../data/raw/cell_lines/keywords.txt',
    ]

    filter_out_track_type = {'Epitope tags', 'GFP'}
    filter_out_cell_type_class = {'Placenta', 'Embryo', 'Pluripotent stem cell', 'No description', 'Embryonic fibroblast'}
    filter_out_cell_type = read_keywords(*keyword_files)

    # 3. Szűrés alkalmazása
    # Először a track type oszlop alapján szűrűnk, mert az a legeffektívebb.
    # Cell type utoljára, mert ott van a legtöbb kulcsszó. Ez hosszabb ideig is futhat.

    # A DataFrame (releváns) oszlopai:
    # TODO: oszlopneves dolgot átnézni (működik, ahogy most van, de kell-e egyáltalán kiírni a fájlokba?
        # 0 - SRX ID
        # 1 és 2 - Törölve (filter_experiment_list miatt)
        # 3 - Track type
        # 4 - Cell type class
        # 5 - Cell type)
    filters = [
        (3, filter_out_track_type, "track type"),
        (4, filter_out_cell_type_class, "cell type class"),
        (5, filter_out_cell_type, "cell type")
    ]
    removed_data = []
    for col_idx, keyword_set, name in filters:
        print(f"Rows before filtering {name}: {len(filtered_df)}")
        filtered_df, removed = filter_data(filtered_df, col_idx, keyword_set)
        print(f"Rows after filtering {name}: {len(filtered_df)}")
        removed_data.append(removed)


    # 4. Törölt adatok mentése
    removed_lines = pd.concat(removed_data, ignore_index=True)
    removed_lines.to_csv('../data/processed/metadata/human_removed_keywords_TEST.tsv', index=False, sep='\t')

    # 5. Megtartott adatok mentése
    filtered_df.to_csv('../data/processed/metadata/human_cleaned.tsv', index=False, sep='\t')
