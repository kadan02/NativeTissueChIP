

def trim_table(input_tsv, output_tsv, variable_names):
    """
    A tsv mappában található metaadatos táblázatokat olvassa be, a felesleges 'key-value' értékeket törli.
    Output: az utóbbi értékek nélküli, átláthatóbb fájl. A törölt érékeket lásd a fields_to_remove list változóban
    # TODO: később beépíteni a filter_metadata_keywords.py scriptbe ezt a functiont, hogy ne kelljen külön lefuttatni
    """
    with open(input_tsv, 'r', encoding="UTF-8") as infile:
        rows = infile.readlines()
    cleaned_rows = []

    for row in rows:
        fields = row.strip().split("\t")
        new_fields = []
        for field in fields:
            clean_field =field.strip().strip('"')
            if not any(clean_field.startswith(var + "=") for var in variable_names):
                new_fields.append(field)
            else:
                print("Deleted: " + field)

        cleaned_rows.append(new_fields)

    # 4. 5. és 6. oszlopok törlése (nem releváns adatok)
    cleaned_rows = [
        [field for i, field in enumerate(row) if i not in {4, 5, 6}]
        for row in cleaned_rows
    ]

    with open(output_tsv, 'w', encoding="UTF-8") as outfile:
        for row in cleaned_rows:
            outfile.write("\t".join(row)  + "\n")

if __name__ == "__main__":

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
                    'chip antibody catalog number','chip antibody manufacturer 1','chip antibody catalog number 1']
    """
    --- Megjegyzések: ---
    Kérdőjeles field-ek:
    donor ID - indikátora lehetnek annak, hogy nem sejtvonalas kísérlet
    source - legtöbb helyen kutatók neve, de túl tág fogalom, lehet van hasznos példa is?
    antibody type fieldek (vegülis ugyanaz mint a track type oszlop)?
    sex - valószínűleg nem releváns
    """

    input_path = '../data/processed/metadata/human_cleaned.tsv'
    output_path = '../data/processed/metadata/human_cleaned_trimmed.tsv'
    trim_table(input_path, output_path, fields_to_remove)
