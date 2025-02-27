import csv
import os

srx_ids = {}
# ignored_lines = set() # debug

with open('human_cleaned_keywords.tsv', mode='r', encoding='utf-8', ) as tsv_file:
    tsv_reader = csv.DictReader(tsv_file, delimiter='\t')
    for row in tsv_reader:
        srx_id = row['0']
        tissue = row['2']
        tf_name = row['1']
        srx_ids[srx_id] = {'tissue': tissue, 'tf_name': tf_name}


id_counter = {}
with open("data/raw/bed/Oth.ALL.50.AllAg.AllCell.bed", 'r', encoding="UTF-8") as input_file:
    next(input_file) # első sor metaadatot tartalmaz a file-ban

    for line in input_file:
        id_start = line.find('ID=') + 3
        id_end = line.find(';', id_start)
        current_srx_id = line[id_start:id_end]

        if current_srx_id in srx_ids:
            tissue = srx_ids[current_srx_id]["tissue"]
            tf_name = srx_ids[current_srx_id]["tf_name"]

            # Output path generálása
            tissue_dir = "bed/" + str(tissue)
            os.makedirs(tissue_dir, exist_ok=True)
            output_path = os.path.join(tissue_dir, f'../data/processed/bed/filtered_{tissue}.bed')

            # Soronként egyedi ID generálása az SRA ID után (run-onként eggyel növekvő szám)
            if current_srx_id not in id_counter:
                id_counter[current_srx_id] = 1
            else:
                id_counter[current_srx_id] += 1
            unique_id = f"{current_srx_id}_{id_counter[current_srx_id]:07d}"

            # oszlopok: chr start end unique_id track_type
            columns = line.split('\t')
            chr_info = f"{columns[0]}\t{columns[1]}\t{columns[2]}\t{unique_id}\t{tf_name}"
            with open(output_path, 'a') as output_file:
                output_file.write(chr_info + '\n')
        # else:
           # ignored_lines.add(current_srx_id)


# with open('log/ignored_lines_' + tissue + ".log", 'w') as log_file:
#    log_file.write('\n'.join(ignored_lines))