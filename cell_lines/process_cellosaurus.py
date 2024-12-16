
def process_cellosaurus_file(input_file, output_file):

    """
    cellosaurus txt link: https://ftp.expasy.org/databases/cellosaurus/cellosaurus.txt

    az ID-kat külön sorokba, külön fájlokba modellorganizmusok szerint.
    egyelőre a különböző modellorganizmusok fájljainak generálásához többször kell futatni, az NCBI_TaxID-t átírva.
    TaxID-k:
    Drosophila melanogaster: 7227
    Homo sapiens: 9606
    Danio rerio: 7955
    Mus musculus: 10090
    Rattus norvegicus: 10116
    """

    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        save_id = False
        cell_line_id = None

        for line in infile:
            line = line.lstrip()
            if line.startswith("ID"):
                cell_line_id = line[3:].strip()
                save_id = False
            elif line.startswith("OX"):
                if "NCBI_TaxID=10116" in line:
                    save_id = True

            elif line.startswith("//"):  # entry vége
                if save_id and cell_line_id:
                    outfile.write(f"{cell_line_id}\n")
                cell_line_id = None
                save_id = False


process_cellosaurus_file("cellosaurus.txt", "cellosaurus_rattus.tsv")