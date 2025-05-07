import pandas as pd
import re

def filter_experiment_list(input_path, genome_type, track_type='TFs and others'):
    """
    input_path: ExperimentList.tab útvonala (ami az összes experiment metaadatait tartalmazza)
    genome_type: Az adott faj genom assembly-jének neve (pl. hg38, mm10)
    track type: pl. 'TFs and others', 'Input control', 'Histone', 'ATAC-seq', lásd: https://chip-atlas.org/peak_browser

    return: genome_type és track_type értékeket tartalmazó sorokból álló DataFrame
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

    return: stringekből álló halmaz
    """
    keywords = set()
    for path in file_paths:
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
    keywords (set): Stringekből álló halmaz, amiket szűrünk az adott oszlopban

    Return: Megtartott és Törölt soroknak megfelelő Dataframe-ek
    """

    # Reguláris expresszió a csak a teljes szavak match-elésére
    keywords_regex = r'\b(?:' + '|'.join(map(re.escape, keywords)) + r')\b'

    # Boolean mask
    has_keyword = data[column_index].astype(str).str.contains(keywords_regex, case=False, na=False)
    removed_rows = data[has_keyword].copy()
    kept_data = data[~has_keyword].copy()

    # Extra oszlop a törölt sorokat tartalmazó Dataframe-be. A kulcsszavat rögzíti, ami alapján törlésre került
    removed_rows['Keyword'] = removed_rows[column_index]

    return kept_data, removed_rows


def remove_duplicate_rows(df, outpath="deleted_duplicate_rows.tsv"):
    """
    Az ID oszlopon kívül teljesen megegyező sorokat törli az első kivételével.

    return: megtartott sorokból álló DataFrame
    """
    # ID-n kívüli oszlopok
    cols = [col for col in df.columns if col != 'ID']

    # Boolean mask
    is_duplicate_of_previous = (df[cols] == df[cols].shift(1)).all(axis=1)

    df_kept = df[~is_duplicate_of_previous].copy()
    print(f"Removed {len(df) - len(df_kept)} duplicate rows.")

    # Törölt sorok mentése
    deleted_rows = df[is_duplicate_of_previous].copy()
    deleted_rows.to_csv(
        outpath,
        sep='\t',
        index=False,
        header=True,
        encoding='utf-8'
    )
    return df_kept

if __name__ == "__main__":

    # Konfiguráció

    # Input táblázat útvonal
    experiment_list_path = '../data/raw/metadata/experimentList.tab'

    # Output útvonalak
    base_output_dir = '../data/processed/metadata/'
    filtered_tsv_path = base_output_dir + 'mouse_filtered.tsv'
    removed_tsv_path = base_output_dir + 'mouse_removed.tsv'
    final_output_path = base_output_dir + 'mouse_preprocessed.tsv'
    deleted_fields_path = base_output_dir + "mouse_deleted_fields.txt"
    deleted_duplicates_path = base_output_dir + "mouse_deleted_duplicate_rows.tsv"

    # Új metaadat oszlop field-jeit ezzel választjuk el majd
    join_delimiter = ' | '

    # filterek megadása
    genome_version = 'mm10'
    track_type_filter = 'TFs and others'

    # Kulcsszavas fájlok betöltése
    keyword_files = [
        '../data/raw/cell_lines/cellosaurus_human.tsv',
        '../data/raw/cell_lines/hg38_added_cell_lines.txt',
        '../data/raw/cell_lines/cell_lines_brenda.txt',
        '../data/raw/cell_lines/keywords.txt',
    ]
    filter_out_track_type = {'Epitope tags', 'GFP'}
    filter_out_cell_type_class = {'Placenta','Embryo', 'Pluripotent stem cell', 'No description','Embryonic fibroblast', 'Breast'}
    filter_out_cell_type = read_keywords(*keyword_files)

    # Felesleges attríbútumnevek megadása, amelyek törlésre kerülnek
    fields_to_remove = ['INSDC status', 'INSDC center alias', 'INSDC center name', 'collection_date', 'biomaterial_provider',
                    'geo_loc_name', 'ENA first public', 'ENA last update', 'External Id', 'INSDC first public', 'INSDC last update',
                    'Submitter Id', 'ENA-FIRST-PUBLIC', 'ENA-LAST-UPDATE','ENA-CHECKLIST', 'antibody vendor', 'vendor',
                    'antibody manufacturer', 'chip antibody vendor','antibody manufacturer', 'antibody catalog id',
                    'ArrayExpress-Species','ArrayExpress-Sex','scientific_name', 'antibody lot number', 'antibody provider',
                    'antibody reference', 'antibody vendorname','antibody vendorid','antibody catalog number', 'lab', 'company',
                    'common name', 'chip antibody', 'antibody', 'chip antibody', 'sex', 'Sex', 'antibody','softwareversion','barcode',
                    'antibody targetdescription','antibody antibodydescription','antibody manufacturer and catalog number',
                    'source','antibody catalog','ChIP','chip-seq antibody','chip antibody details','labversion','labversion description',
                    'antibody brand','chip antibody manufacturer','chip ab','chip-antibody','antibody maker','chip target',
                    'sample name','ArrayExpress-Immunoprecipitate','ArrayExpress-CellType','chip antibody info','antibody vendor/provider',
                    'chip antibody catalog number','chip antibody manufacturer 1','chip antibody catalog number 1','ancestry',
                     'purification target','antibody source','library type','antibodies','chip epitope','antibody lot/batch number']
    print(f"Number of fields to remove: {len(fields_to_remove)}")

    # Konfiguráció vége

    # 1. ExperimentList.tab szűrése, DataFrame létrehozása
    print(f"Filtering {experiment_list_path} for genome '{genome_version}' and track type '{track_type_filter}'...")
    filtered_df = filter_experiment_list(experiment_list_path, genome_version, track_type_filter)
    print(f"Initial rows after genome/track filtering: {len(filtered_df)}")

    # 2.A szűrendő kategóriák párosítása az oszlopokkal
    current_columns = filtered_df.columns.tolist()
    print(f"Columns after initial filter: {current_columns}")
    col_map = {
        'track_type': current_columns[1],
        'cell_type_class': current_columns[2],
        'cell_type': current_columns[3]
    }
    filters = [
        (col_map['track_type'], filter_out_track_type, "Track type"),
        (col_map['cell_type_class'], filter_out_cell_type_class, "Cell type class"),
        (col_map['cell_type'], filter_out_cell_type, "Cell type")
    ]
    removed_data = []
    for col_idx, keyword_set, name in filters:
        print(f"Rows before filtering {name}: {len(filtered_df)}")
        filtered_df, removed = filter_data(filtered_df, col_idx, keyword_set)
        print(f"Rows after filtering {name}: {len(filtered_df)}")
        removed_data.append(removed)

    # 3. Kulcsszavas szűrés a standardizált oszlopokon (filter_data function meghívása)
    print("\nStarting keyword filtering...")
    removed_data_list = []
    df_after_keyword_filters = filtered_df.copy()

    for col_name, keyword_set, name in filters:
        rows_before = len(df_after_keyword_filters)
        print(f"Rows before filtering '{name}' (column '{col_name}'): {rows_before}")
        df_after_keyword_filters, removed = filter_data(df_after_keyword_filters, col_name, keyword_set)
        rows_after = len(df_after_keyword_filters)
        print(f"Rows after filtering '{name}': {rows_after} ({rows_before - rows_after} removed)")
        if not removed.empty:
            removed['Filter_Type'] = name
            removed_data_list.append(removed)

    # 4. Törölt adatok mentése
    if removed_data_list:
        all_removed_data = pd.concat(removed_data_list, ignore_index=True)
        print(f"\nSaving {len(all_removed_data)} removed rows to: {removed_tsv_path}")
        all_removed_data.to_csv(removed_tsv_path, index=False, sep='\t', encoding='utf-8')
    print(f"Saving intermediate data ({len(df_after_keyword_filters)} rows) to: {filtered_tsv_path}")
    df_after_keyword_filters.to_csv(filtered_tsv_path, index=False, sep='\t', encoding='utf-8')

    # 5. Felesleges "key=value" fieldek törlése
    df_to_process = pd.read_csv(filtered_tsv_path, sep='\t', dtype=str, keep_default_na=False)
    deleted_log_entries = []
    def clean_field(field):
        stripped = field.strip().strip('"')
        for key in fields_to_remove:
                prefix = key + "="
                if stripped.startswith(prefix):
                    deleted_log_entries.append(field)
                    return None
        return field

    print("Applying key=value field cleaning...")
    df_processed = df_to_process.applymap(clean_field)

    if deleted_log_entries:
        print(f"Logging {len(deleted_log_entries)} removed key=value entries to {deleted_fields_path}")
        with open(deleted_fields_path, 'w', encoding='utf-8') as logfile:
            for entry in deleted_log_entries:
                logfile.write(entry + "\n")

    current_processed_columns = df_processed.columns.tolist()
    id_col_final = current_processed_columns[0]
    tf_col_final = current_processed_columns[1]
    class_col_final = current_processed_columns[2]
    type_col_final = current_processed_columns[3]

    cols_to_combine_final = current_processed_columns[7:]
    print(f"Columns identified for final structure: ID='{id_col_final}', TF='{tf_col_final}', Class='{class_col_final}', Type='{type_col_final}'")
    print(f"Columns to combine into Metadata: {cols_to_combine_final}")

    # 6. Metaadat oszlopok összefűzése
    def combine_metadata_row(row):
        values = []
        for col in cols_to_combine_final:
            cell_value = row[col]
            if pd.notna(cell_value) and str(cell_value).strip():
                values.append(str(cell_value).strip())
        return join_delimiter.join(values)
    df_processed['Metadata'] = df_processed.apply(combine_metadata_row, axis=1)

    final_df = df_processed[[id_col_final, tf_col_final, class_col_final, type_col_final, 'Metadata']].copy()
    final_df.rename(columns={
        id_col_final: 'ID',
        tf_col_final: 'Transcription_Factor',
        class_col_final: 'Cell_type_class',
        type_col_final: 'Cell_type'
    }, inplace=True)

    # 7. duplicate sorok törlése
    final_df = remove_duplicate_rows(final_df, deleted_duplicates_path)

    # 8. adatok mentése
    print(f"Saving final processed data ({len(final_df)} rows) to: {final_output_path}")
    final_df.to_csv(final_output_path, sep='\t', index=False, encoding='utf-8')