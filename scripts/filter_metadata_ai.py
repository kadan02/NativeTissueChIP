from datetime import datetime
from openai import OpenAI
import distance
import re
import json


# https://doc.genai.science-cloud.hu/api/
client = OpenAI(base_url="https://genai.science-cloud.hu/ollama/v1/", api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImNhZDBhODI4LTE4NzYtNGE3NC1iZTFkLWYzMDEyNjJmY2M5YyJ9.s1LS0hCfcCOMnilwSyf67hwHEmeN9piZTMTV7aMGcKQ")


def group_rows(tsv_file, max_distance=6, max_rows=6):
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

    groups = []

    with open(tsv_file, "r", encoding="utf-8") as file:
        rows = file.read().splitlines()

    # Csak 2-4 oszlop adatait vizsgáljuk
    core_data = []
    for row in rows:
        parts = row.split('\t')
        core = "\t".join(parts[1:4])
        core_data.append(core)

    # Levenshtein távolság kalkulálása soronként
    current_group = [rows[0]]
    for i in range(1, len(rows)):
        prev_core = core_data[i - 1]
        curr_core = core_data[i]
        d = distance.levenshtein(prev_core, curr_core)

        if d > max_distance or len(current_group) >= max_rows:
            groups.append(current_group)  # Jelenlegi csoport mentése, ha a távolság túl van lépve
            current_group = [rows[i]]  # Új csoport
        else:
            current_group.append(rows[i])  # Jelenlegi csoport folytatása

    # Utolsó sor(ok) mentése a táblázatban
    if current_group:
        groups.append(current_group)

    return groups


def api_request(group, output_log):
    instructions = (
        "TASK:\n"
        "Extract the IDs of NATIVE sample sequencings from the DATA.\n"
        "The DATA consists of ChIP-Seq metadata from a TSV file. Each row is one sequencing. The first column is the id.\n\n"

        "DEFINITION OF NATIVE SAMPLES:\n"
        "- Native samples mimic normal physiological conditions.\n"
        "- They come from healthy, unmodified, and drug-free specimens.\n"
        "- Wild-type (WT), untreated, and control samples are usually native; but verify for any non-native indicators.\n\n"
        #"- Note: Transcription factor names are not indicative, ignore them.\n\n"  (Kommentelve mert nem túl hatásos) 

        "NON-NATIVE INDICATORS:\n"
        "- Any immortalized cell line name.\n"
        "- Keywords such as:\n"
        "   - 'cancer'\n"
        "   - 'tumor'\n"
        "   - 'treated'\n"
        "   - 'knockout'\n"
        "   - 'fetal'\n"
        "   - 'embryonic'\n"
        "- and any of their synonyms or abbreviations.\n\n"
        "- Mention of a regular human cell line (e.g., 'ED cells') or primary cell line is NOT a non-native indicator.\n"
        #"- Breast cells' is NOT A NON-NATIVE INDICATOR by itself.\n"
        #"- Note: 'Differentiated' is NOT A NON-NATIVE INDICATOR by itself.\n\n" (Kommentelve mert egyáltalán nem  hatásos)
        
        "IMPORTANT: Return only the JSON object, exactly in the format specified below, with no extra text or formatting.\n"
        'ANSWER FORMAT:  {"native_ids": ["<id1>", "<id2>"]}\n'
        'Answer example 1: {"native_ids": []}\n'
        'Answer example 2: {"native_ids": ["DRX044425", "DRX044426"]}\n\n'
        
        "DATA:\n"
    )

    prompt = instructions + "\n".join(group)

    completion = client.chat.completions.create(
        model="mistral-small:24b",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    response = completion.choices[0].message.content
    with open(output_log, 'a', encoding='utf-8') as f:
        f.write(response + "\n")

    print(response)


def write_new_tables(api_response_file, metadata, native_metadata, non_native_metadata):
    """
    A JSON tömbön belüli "native_ids":  kulcsokhoz tartozó értékeket egy új fájlba írja az API response fájlból.

    A JSON formátumot néha elrontja az AI, ezeket az exception alapján manuálisan debuggolni kell.
    """

    with open(api_response_file, "r", encoding="utf-8") as f:
        content = f.read()

    # JSON blokk markerek törlése
    content = content.replace("```json", "").replace("```", "")

    # Blokkok tartalmának extraktálása
    json_objects = re.findall(r'\{.*?\}', content, re.DOTALL)

    native_ids = set()

    for obj in json_objects:
        try:
            data = json.loads(obj)
            if "native_ids" in data and isinstance(data["native_ids"], list):
                for id_val in data["native_ids"]:
                    clean_id = id_val.strip().strip('",')
                    if clean_id:
                        native_ids.add(clean_id)
        except json.JSONDecodeError as e:
            print(f"Skipping invalid JSON:\n{obj}\n{e}\n")   # Hibás sorokat debugolni kell

    print(f"{len(native_ids)} unique native IDs found in API responses.")

    # 2 új táblázat létrehozása. Egyikbe csak a natívok íródnak, másikba a nem natívok
    with open(metadata, "r", encoding="utf-8") as input_metadata, open(native_metadata, "w", encoding="utf-8") as native_output, open(non_native_metadata, "w", encoding="utf-8") as non_native_output:
        for line in input_metadata:
            first_column = line.split("\t")[0]
            if first_column in native_ids:
                native_output.write(line)
            else:
                non_native_output.write(line)

    print(f"Created tables: {native_metadata} and {non_native_metadata}")


def process_responses(input_tsv, output_log):
    groups = group_rows(input_tsv, max_distance=6, max_rows=6)
    print(f"Total groups created: {len(groups)}")

    for i, group in enumerate(groups):
        print(f"Sending group {i + 1}/{len(groups)} with {len(group)} rows to API...")
        api_request(group, output_log)


if __name__ == '__main__':
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    input_tsv_path = "../data/processed/human_cleaned_keywords.tsv"  # az összes metaadatot tartalmazó fájl
    api_response_path = f"data/logs/ai_responses/{timestamp}_mistral-small24b.json"      # API válaszok
    native_table_path = f"results/{timestamp}_native_ids.tsv"              # Csak natív ID-s metaadatok
    non_native_table_path = f"results/{timestamp}_non_native_ids.tsv"      # Csak nem-natív ID-s metaadatok

    process_responses(input_tsv_path, api_response_path)
    write_new_tables(api_response_path, input_tsv_path, native_table_path, non_native_table_path)