from datetime import datetime
from openai import OpenAI
import distance
import re
import json
import os
import logging

# TODO:
#  - replicate entryt törölni a trim_tsv.py-al, mert úgyis csekkoljuk már az ugyanolyan sorokat.
#  - A levenshtein távolság alapján csoportosító functiont külön functionba írni, és lehetőve tenni egy boolean-el,
#  hogy könnyen futtatható legyen távolság alapján történő csoportosítással és anélkül is
#  - megpróbálni lefuttatni nagyobb méretű csoportokkal
#  - fine tuning? https://docs.mistral.ai/capabilities/finetuning/
#  - function calling: https://docs.mistral.ai/capabilities/function_calling/
#  - Kipróbálni lépcsősen beadni külön promptokat mindig 1-1 dologra fókuszálva.


# Problémás klasszifikációk? naïve immunsejtek; stimulated és differentiated sejtek 1-2 helyen még pontatlan


def log_message(message):
    logging.info(message)


def group_rows(tsv_file, max_distance=6, max_rows=6) -> list:
    """
    A metaadatokat tartalmazó TSV fájl egymást követő sorait csoportosítja a Levehnstein-távolságuk alapján.

    Paraméterek:
        - tsv_file: A metaadatokat tartalmazó TSV fájl útvonala.
        - max_distance: Az egymást követő sorok közötti maximális Levenshtein-távolság. Ha ez túl van lépve, az adott
         sor új csoportba kerül
        - max_rows: A sorok csoportonkénti maximális száma (6+ soros inputoknál a mistral-small:24b modell már
        gyakran hibázik, vagy nem értelmezhető outputot generál).

    Return:
        groups (list): A hasonló sorokat tartalmazó listák listája
    """
    log_message(f"Reading TSV file: {tsv_file}")
    with open(tsv_file, "r", encoding="utf-8") as file:
        rows = file.read().splitlines()

    groups = []
    core_data = []  # 2-4 oszlopok adatai, ez alapján lesz a távolság számolva.
    processed_rows = [] # Minden oszlop a másodikon kívül, amit LLM-nek nem fogunk tovább adni, mert nem releváns (TF név).
    current_data_list = []  # Első és második oszlopon kívül az adatok soronként, összehasonlítás miatt

    for row in rows:
        parts = row.split('\t')
        core = "\t".join(parts[1:4])
        core_data.append(core)

        processed_parts = parts[:1] + parts[2:]
        processed_row = "\t".join(processed_parts)
        processed_rows.append(processed_row)
        current_data = "\t".join(parts[2:]) if len(parts) >= 3 else ""
        current_data_list.append(current_data)

    seen_data = set()
    seen_data.add(current_data_list[0])
    current_group = [processed_rows[0]] # Inicializálás

    # Levenshtein távolság kalkulálása. Mindig a következő sort az előzőhöz hasonlítjuk
    for i in range(1, len(rows)):
        current_data = current_data_list[i]

        if current_data in seen_data:
            print(f"Skipping row {i} as it duplicates existing data.")
            log_message(f"Skipping row {i} as it duplicates existing data.")
            continue

        prev_core = core_data[i - 1]
        curr_core = core_data[i]
        d = distance.levenshtein(prev_core, curr_core)
        print(f"Comparing row {i - 1} with row {i} → Distance: {d}")
        log_message(f"Comparing row {i - 1} with row {i} → Distance: {d}")


        if d > max_distance or len(current_group) >= max_rows:
            print(f"New group created at row {i}")
            log_message(f"New group created at row {i}")
            groups.append(current_group)  # Jelenlegi csoport mentése, ha a távolság túl van lépve
            current_group = [processed_rows[i]]  # Új csoport
            seen_data.add(current_data)

        else:
            print(f"Adding row {i} to current group.")
            log_message(f"Adding row {i} to current group.")
            current_group.append(processed_rows[i])  # Jelenlegi csoport folytatása
            seen_data.add(current_data)

    # Utolsó sor(ok) mentése a táblázatban
    if current_group:
        groups.append(current_group)
        print(f"Final group added with {len(current_group)} rows.")
        log_message(f"Final group added with {len(current_group)} rows.")

    print(f"Total groups created: {len(groups)}")
    log_message(f"Total groups created: {len(groups)}")

    return groups


def api_request(group, output_log, output_prompt, url, key):

    # prompt guide = https://docs.mistral.ai/guides/prompting_capabilities/
    # json guide = https://docs.mistral.ai/capabilities/structured-output/json_mode/

    instructions = (
"""# Task Overview
Classify sequencing samples as NATIVE or NON-NATIVE based on the provided DATA. The DATA consists of ChIP-Seq metadata from a TSV file, where each row represents one sequencing entry. The first column is the ID.

## Definitions
### Native Samples
- **Normal Physiological Conditions**: Mimic normal physiological conditions.
- **Healthy Specimens**: Come from healthy, unmodified, and drug-free specimens.
- **Wild-Type (WT)**, Untreated, and Control samples are usually native.

### Non-Native Samples
- **Immortalized Cell Lines**: Contain an immortalized cell line name. Mention of a regular human cell line (e.g., 'ED cells') or primary cell line is NOT a non-native indicator.
- **Modifications**, such as:
  - 'cancer', 'tumor'
  - 'treated'
  - 'knockout', KO, KD
  - 'fetal', 'embryonic'
  - Any synonyms or abbreviations of these terms.
- **Not Non-Native**: 'Activated' and 'differentiated' are NOT non-native indicators.
- **Mixed Indicators**: If a sample has both native and non-native indicators, classify as non-native.

## Answer Format
Return only a valid JSON array with this exact structure:
```json
[
  {"id": "<sample_id>", "metadata": "<sample_metadata>", "native": <True/False>},
  {"id": "<sample_id>", "metadata": "<sample_metadata>", "native": <True/False>}
]

### Answer examples:
[
  {"id": "SRX12345", "metadata": "wild-type, untreated, control", "native": true},
  {"id": "SRX67890", "metadata": "wild-type, but treated", "native": false},
  {"id": "SRX98765", "metadata": "primary cells, embryonic", "native": false}
]

## DATA:

"""
    )

    # Prompt írása külön fájlba az adatok nélkül
    with open(output_prompt,'w', encoding='utf-8') as p:
        p.write(instructions)

    prompt = instructions + "\n".join(group)
    log_message(f"Sending API request for group with {len(group)} rows.")

    # https://doc.genai.science-cloud.hu/api/
    client = OpenAI(base_url=url, api_key=key)
    completion = client.chat.completions.create(
        model="mistral-small:24b",
        messages=[
            {"role": "system", "content": "You are an assistant specialized in analyzing biological data. You only respond in valid JSON format."},
            {"role": "user", "content": prompt}
        ],
        # info: https://docs.mistral.ai/guides/sampling/
        temperature= 0,
        # top_p=0.1 ha temperature != 0 TODO: ezzel kísérletezni
        seed = 342
    )
    response = completion.choices[0].message.content
    log_message(f"API request completed for group with {len(group)} rows.")
    with open(output_log, 'a', encoding='utf-8') as f:
        f.write(response + "\n")

    print(response)


def read_response_file(json_file,errors_log):

    log_message(f"Reading JSON response file: {json_file}")
    with open(json_file,'r', encoding='utf-8') as f:
        content = f.read().replace("```json", "").replace("```", "").strip()

    content = content.replace("\t", "\\t")
    content = content.replace('True', 'true').replace('False', 'false')
    content = content.replace('"True"', 'true').replace('"False"', 'false')


    json_blocks = re.findall(r'\[\s*{.*?}\s*]', content, re.DOTALL)
    json_objects = []

    with open(errors_log,'w', encoding='utf-8') as errors:
        for block in json_blocks:
            try:
                parsed_block = json.loads(block)
                if isinstance(parsed_block, list):
                    json_objects.extend(parsed_block)
            except json.JSONDecodeError as e:
                errors.write(f"JSON parsing error: {e}\nRaw JSON block: {block}")
                print(f"JSON parsing error: {e}\nRaw JSON block: {block}")

    print(f"Extracted {len(json_objects)} JSON objects.")
    log_message(f"Extracted {len(json_objects)} JSON objects.")

    return json_objects


def write_new_tables(json_file, errors, metadata, native_metadata, non_native_metadata):

    json_objects = read_response_file(json_file, errors)

    native_ids = set()
    non_native_ids = set()

    for obj in json_objects:
        if "id" in obj and "native" in obj:
            if obj["native"]:
                native_ids.add(obj["id"].strip())
            elif not obj["native"]:
                non_native_ids.add(obj["id"].strip())

    print(f"{len(native_ids)} unique native IDs found in API responses.")

    # 2 új táblázat létrehozása. Egyikbe csak a natívok íródnak, másikba a nem natívok
    with open(metadata, "r", encoding="utf-8") as input_metadata, open(native_metadata, "w", encoding="utf-8") as native_output, open(non_native_metadata, "w", encoding="utf-8") as non_native_output:
        for line in input_metadata:
            first_column = line.split("\t")[0]
            if first_column in native_ids:
                native_output.write(line)
            else:
                non_native_output.write(line)

    log_message(f"Created tables: {native_metadata} and {non_native_metadata}")
    print(f"Created tables: {native_metadata} and {non_native_metadata}")


def process_responses(input_tsv, output_log, output_prompt, url, key):
    groups = group_rows(input_tsv, max_distance=6, max_rows=6)

    log_message(f"Total groups created: {len(groups)}")
    print(f"Total groups created: {len(groups)}")


    for i, group in enumerate(groups):
        log_message(f"Processing group {i + 1}/{len(groups)}")
        print(f"Sending group {i + 1}/{len(groups)} with {len(group)} rows to API...")
        api_request(group, output_log, output_prompt, url, key)


if __name__ == '__main__':

    # Output fájlok ebbe a mappába fognak íródni
    # run_name = "" ha timestamp-et szeretnénk használni
    run_name = input("Output directory name (Leave empty for name based on current time): ")

    if run_name == "":
        run_name = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    dir_name = "../data/processed/ai_filtering/" + run_name

    try:
        os.mkdir(dir_name)
        print(f"Directory '{dir_name}' created successfully.")
    except FileExistsError:
        print(f"Directory '{dir_name}' already exists.")
    except PermissionError:
        print(f"Permission denied: Unable to create '{dir_name}'.")

    # Logging setup
    log_file = f"{dir_name}/logs.log"
    logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s")

    # Fájlok útvonalai
    input_tsv_path = "../data/processed/metadata/human_cleaned_trimmed.tsv"    # Az összes metaadatot tartalmazó fájl
    json_path = f"{dir_name}/responses.json"                            # API válaszok
    errors_log_path = f"{dir_name}/json_errors.log"
    prompt_path = f"{dir_name}/prompt.txt"                                      # A prompt ide íródik
    native_table_path = f"{dir_name}/native_ids.tsv"                            # Csak natív ID-s metaadatok
    non_native_table_path = f"{dir_name}/non_native_ids.tsv"                    # Csak nem-natív ID-s metaadatok

    server_url = ""
    api_key = ""

    process_responses(input_tsv_path, json_path, prompt_path, server_url, api_key)
    write_new_tables(json_path, errors_log_path, input_tsv_path, native_table_path, non_native_table_path)

    log_message("Processing completed successfully.")
