import csv
import os

# Konfiguráció
native_metadata_table = "../data/processed/classification/mistral-small31-24b_full/native_classified.tsv"
tissue_bed_file = "../data/raw/bed/Oth.Utr.05.AllAg.AllCell.bed"


srx_ids = {}
# ignored_lines = set() # debug

with open(native_metadata_table, mode='r', encoding='utf-8', ) as tsv_file:
    tsv_reader = csv.DictReader(tsv_file, delimiter='\t')
    for row in tsv_reader:
        srx_id = row['ID']
        tissue = row['Cell_type_class']
        tf_name = row['Transcription_Factor']
        srx_ids[srx_id] = {'Cell_type_class': tissue, 'Transcription_Factor': tf_name}


id_counter = {}
output_files = {}
with open(tissue_bed_file, 'r', encoding="UTF-8") as input_file:
    next(input_file) # első sor metaadatot tartalmaz a file-ban

    for line in input_file:
        id_start = line.find('ID=') + 3
        id_end = line.find(';', id_start)
        current_srx_id = line[id_start:id_end]

        if current_srx_id in srx_ids:
            tissue = srx_ids[current_srx_id]["Cell_type_class"]
            tf_name = srx_ids[current_srx_id]["Transcription_Factor"]

            # Output path generálása
            output_dir = "../data/processed/bed/"
            output_filename = f'filtered_{tissue}.bed'
            output_file_path = os.path.join(output_dir, output_filename)
            os.makedirs(output_dir, exist_ok=True)

            # Soronként egyedi ID generálása az SRA ID után (run-onként eggyel növekvő szám)
            if current_srx_id not in id_counter:
                id_counter[current_srx_id] = 1
            else:
                id_counter[current_srx_id] += 1
            unique_id = f"{current_srx_id}_{id_counter[current_srx_id]:07d}"

            # oszlopok: chr start end unique_id track_type
            columns = line.split('\t')
            chr_info = f"{columns[0]}\t{columns[1]}\t{columns[2]}\t{unique_id}\t{tf_name}"

            if output_file_path not in output_files:
                output_files[output_file_path] = open(output_file_path, 'a', encoding='utf-8')
                print(f"Opening {output_file_path} for appending...")
            output_files[output_file_path].write(chr_info + '\n')
        # else:
            # ignored_lines.add(current_srx_id)


# with open('log/ignored_lines_' + tissue + ".log", 'w') as log_file:
#    log_file.write('\n'.join(ignored_lines))

for f_handle in output_files.values():
    f_handle.close()