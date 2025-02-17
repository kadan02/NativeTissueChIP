from datetime import datetime
from openai import OpenAI
import distance
import re

# https://doc.genai.science-cloud.hu/api/
client = OpenAI(base_url="", api_key="")


def group_rows(tsv_file, max_distance, max_rows):
    """
    A metaadatokat tartalmazó TSV fájl egymást követő sorait csoportosítja a Levehnstein-távolságuk alapján.

    Paraméterek:
        tsv_file (str): A metaadatokat tartalmazó TSV fájl útvonala.
        max_distance (int): Az egymást követő sorok közötti maximális Levenshtein-távolság. Ha ez túl van lépve, az adott
         sor új csoportba kerül
        max_rows (int): A sorok csoportonkénti maximális száma (6+ soros inputoknál a mistral-small:24b modell már
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
        "TASK:"
        "Extract the IDs of NON-NATIVE sample sequencings from the DATA.\n"
        "The DATA consists of ChIP-Seq metadata from a TSV file. Each row is one sequencing. The first column is the id.\n\n"

        "DEFINITION OF NATIVE SAMPLES:\n"
        "- Native samples mimic normal physiological conditions.\n"
        "- They come from healthy, unmodified, and drug-free specimens.\n"
        "- Wild-type (WT), untreated, and control samples are usually native; but verify for any non-native indicators.\n\n"
        #"- Note: Transcription factor names are not indicative, ignore them.\n\n"  (Kommentelve mert nem túl hatásos) 

        "NON-NATIVE INDICATORS:\n"
        "- Keywords such as 'cancer', 'tumor', 'treated', 'knockout', 'fetal', 'embryonic' (including synonyms/abbreviations).\n"
        "- Any immortalized cell line name.\n"
        "- Note: Mention of a regular human cell line (e.g., 'ED cells') or primary cell line is NOT A NON-NATIVE INDICATOR.\n"
        "- Note: 'Breast cells' is NOT A NON-NATIVE INDICATOR by itself.\n"
        #"- Note: 'Differentiated' is NOT A NON-NATIVE INDICATOR by itself.\n\n" (Kommentelve mert egyáltalán nem  hatásos)

        "ANSWER FORMAT:\n"
        "Return only the JSON object, exactly in the format specified below, with no extra text or formatting.\n"
        
        "{\n"
        "  \"non_native_samples\": [\n"
        "    {\n"
        "      \"id\": \"<id1>\",\n"
        "      \"reason\": \"<short reason>\"\n"
        "    },\n"
        "    {\n"
        "      \"id\": \"<id2>\",\n"
        "      \"reason\": \"<short reason>\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        
        "Example:\n"
        "{\n"
        "  \"non_native_samples\": [\n"
        "    {\n"
        "      \"id\": \"SRX111111\",\n"
        "      \"reason\": \"Null genotype\"\n"
        "    },\n"
        "    {\n"
        "      \"id\": \"SRX222222\",\n"
        "      \"reason\": \"Treated with calcium\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
                
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


def process_tsv(input_tsv, output_log):
    groups = group_rows(input_tsv, max_distance=6, max_rows=6)
    print(f"Total groups created: {len(groups)}")

    for i, group in enumerate(groups):
        print(f"Sending group {i + 1}/{len(groups)} with {len(group)} rows to API...")
        api_request(group, output_log)


def extract_ids_and_reasons(api_response_file, output_file):
    """
    A JSON tömbön belüli "id": és "reason": kulcsokhoz tartozó értékeket egy új fájlba írja az API response fájlból.

    Output_file:
     Első oszlop: "id"
     Második oszlop: "reason"

    A JSON formátumot néha elrontja az AI, viszont a reguláris kifejezéssel kiküszöbölhető többnyire a probléma.
    """

    with open(api_response_file,'r',encoding='utf-8') as f:
        content = f.read()
    print("Starting ID extraction from API response file.\nInput file content length:", len(content))


    # Regex magyarázat:
    # \s* - tetszőleges számú whitespace karakterek
    # "([^"]+)" - az idézőjelek közötti értékek rögzítése
    pattern = re.compile(r'"id"\s*:\s*"([^"]+)"\s*,\s*"reason"\s*:\s*"([^"]+)"', re.DOTALL)

    matches = pattern.findall(content)
    print("Found", len(matches), "ID and reason pairs.")

    with open(output_file,'w', encoding='utf-8') as f:
        f.write("ID\tReason\n")
        for id, reason in matches:
            clean_id = id.strip().strip("<>").lstrip("-")
            f.write(clean_id + "\t")
            f.write(reason + "\n")

    print("Extraction complete. Results written to:", output_file)


if __name__ == '__main__':
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    input_tsv_path = "tsv/hg38_native_runs.tsv"
    api_response_path = f"logs/{timestamp}_mistral-small24b.txt"
    extracted_ids_tsv_path = f"tsv/{timestamp}_non_native_ids.txt"

    process_tsv(input_tsv_path, api_response_path)
    extract_ids_and_reasons(api_response_path,extracted_ids_tsv_path)