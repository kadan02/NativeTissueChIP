

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
                print("Törölve: " + field)

        cleaned_rows.append(new_fields)

    # A maximum nem üres stringet tartalmazó oszlopszám az összes új sor közül. A többi sor eddig lesz feltöltve üres
    # karakterekkel, hogy egységes oszlopszámú legyen
    col_number = max(len(row) for row in cleaned_rows)
    print("Max column: " + str(col_number))

    # Fejléc 0-tól (max oszlopszám - 1) -ig
    new_header = "\t".join(str(i) for i in range(col_number))

    with open(output_tsv, 'w', encoding="UTF-8") as outfile:
        outfile.write(new_header + "\n")
        for row in cleaned_rows:
            row.extend([""] * (col_number - len(row)))
            outfile.write("\t".join(row)  + "\n")


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

input_path = ''
output_path = ''
trim_table(input_path, output_path, fields_to_remove)
