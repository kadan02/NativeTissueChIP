# Segédfunkciók a classification_main.py scripthez.

import re
import logging
import json
from rapidfuzz import fuzz
from classification_config import LLM_INSTRUCTIONS


def clean_keywords(keyword_dict):
    """
    A kulcsszavakat 'standardizált' állapotba formázza, azaz minden számon és betűn kivülí karaktert
    (szóközt beleértve) eltávolít és kisbetűs stringként tárolja a neveket egy új dict-ben.

    A find_keywords function később a cleaned_keywords dict-et veszi be inputként.
    """
    cleaned_keywords = {}
    for category, data in keyword_dict.items():
        for kw in data['keywords']:
            kw_clean = re.sub(r'[^a-zA-Z0-9]', '', kw.lower())
            if kw_clean:
                cleaned_keywords[kw_clean] = (kw, category, data['weight'], data['classification'])
    return cleaned_keywords


def extract_key_value_pairs(metadata):
    """
    'Kulcs=érték' párosokat keres egy stringből és tárol el egy dict-ben. Az adott párosok '|' karakterekkel vannak elválasztva.
        """
    pairs = {}
    for pair in metadata.split('|'):
        pair = pair.strip()
        parts = pair.split('=')
        if len(parts) == 2:
            key = parts[0].strip().lower()
            value = parts[1].strip()
            pairs[key] = value
    return pairs


def find_keywords(cleaned_keywords, key_value_pairs, threshold=85, max_len=2):
    """
    Kulcs=érték párosokból az ÉRTÉKEKET a megadott KULCSSZAVAKKAL matcheli a rapidfuzz könyvtár segítségével.
    A hasonlóság határa és a maximum összehasonlítandó, egymást követő szavak értékei megadhatóak.
    A max_len-t a legtöbb szóból álló kulcsszó (kifejezés) szavainak számára értemes állítani.

    Return: Egy szótárakból álló lista, amely az alábbi részleteket tárolja a matchek-ről:
        'matched_text'
        'keyword'
        'category'
        'score'
        'weight'
        'classification'
        'source_key'

    Ha a határértéken felül nincsen match, akkor üres lista.
    """
    matches = []

    for key, value in key_value_pairs.items():
        logging.debug(f"Searching keywords:'{key}': '{value}'")

        # Tokenizáció és standardizálás
        # pl.: "Blood-derived T-cell samples." -> ['blood-derived', 't-cell', 'samples']
        tokens = re.findall(r'\b[a-zA-Z0-9-]+\b', value.lower())
        i = 0
        while i < len(tokens):
            # Window: belső loop a tokeneken
            best_match_in_window = None

            # Fontos, hogy először a hosszabb kifejezéseket ellenőrizzük.
            # Ez biztosítja, hogy pl. a "cell line" kifejezés nagyobb prioritást kap, mint a "cell"
            for window in range(max_len, 0, -1):
                if i + window > len(tokens):
                    continue
                span_tokens = tokens[i:i+window]
                span_text = ' '.join(span_tokens)

                # Hasonlóan mint a kulcsszavaknál, a nem betű/szám karaktereket eltávolítjuk
                span_clean = re.sub(r'[^a-zA-Z0-9]', '', span_text)

                # Hasonlóság megállapítása kulcsszavanként
                for cl_clean, kw_data in cleaned_keywords.items():
                    score = fuzz.ratio(span_clean, cl_clean)
                    if score >= threshold:
                        original_keyword, category, weight, classification = kw_data
                        match_info = {
                            'matched_text': span_text,
                            'keyword': original_keyword,
                            'category': category,
                            'score': score,
                            'weight': weight,
                            'classification': classification,
                            'source_key': key
                        }
                        if best_match_in_window is None or score > best_match_in_window['score']:
                             best_match_in_window = match_info

            if best_match_in_window:
                matches.append(best_match_in_window)
                # Előrelépés a match hosszával
                best_match_len = len(best_match_in_window['matched_text'].split())
                i += best_match_len
            else:
                i += 1

    return matches


def classify_based_on_keywords(matches):
    """
    A kulcsszavak súlyai/prioritásai alapján az osztályozás.

    TODO:A konfidencia szint egyelőre redundáns.

    Return: az osztályozás (native/non-native), konfidencia szint, és osztályozás oka.
    """
    if not matches:
        return 'unknown', 0, "No keywords"

    # A legmagasabb súlyú match keresése (gyakorlatilag a nem-natív priorizálása)
    best_match = max(matches, key=lambda x: x['weight'])

    classification = best_match['classification']
    confidence = best_match['weight']
    reason = f"Highest weight keyword: '{best_match['keyword']}' (category: {best_match['category']}, score: {best_match['score']})"

    return classification, confidence, reason


def classify_with_llm(row_id, sample_data, client, model_name, output_prompt_file=None, response_log_file=None):
    """
    meghív egy LLM-et, hogy 1 stringet (1 db sort) osztályozzon. Az LLM-nek valid JSON formátumban kell válaszolnia.

    TODO: konfidencia szint itt is redundáns egyelőre

    Return: az osztályozás értéke (native/non-native), konfidencia szint, és osztályozás oka.
    """
    logging.info(f"Attempting LLM classification for ID: {row_id}, Text: '{sample_data}'")

    messages_for_api = [
        {"role": "system", "content": LLM_INSTRUCTIONS},
        {"role": "user", "content": sample_data}
    ]

    # Prompt kiírása fájlba (ellenőrizhetőség)
    if output_prompt_file:
        write_prompt = f"System Prompt:\n{LLM_INSTRUCTIONS}\n\nUser Prompt:\n{sample_data}"
        with open(output_prompt_file, 'w', encoding='utf-8') as p:
            p.write(write_prompt)

    try:
        # API request
        completion = client.chat.completions.create(
            model=model_name, messages=messages_for_api, temperature=0, seed=100
        )
        response_content = completion.choices[0].message.content
        logging.debug(f"LLM Response for {row_id}: {response_content}")

        # JSON keresées thinking blokk után, ha thinking modelt akarunk használni
        json_part = response_content
        think_end_tag = "</think>"
        if think_end_tag in response_content:
            parts = response_content.split(think_end_tag, 1)
            if len(parts) > 1:
                json_part = parts[1]

        # Válaszok kiírása fájlba
        if response_log_file:
            try:
                response_log_file.write(f"--- LLM Response for ID: {row_id} ---\n{response_content}\n\n")
                response_log_file.flush()
            except IOError as e: logging.warning(f"Could not write LLM response for {row_id}: {e}")
        cleaned_response = json_part.replace("```json", "").replace("```", "").strip()

        # JSON-ból adatok kezelése. Ha esetleg hibás, akkor log-ban warning
        try:
            parsed_json = json.loads(cleaned_response)
            if isinstance(parsed_json, dict) and "id" in parsed_json and "native" in parsed_json:
                 is_native = parsed_json.get("native", None)
                 classification = 'native' if is_native is True else 'non-native' if is_native is False else 'unknown'
                 if classification == 'unknown':
                      logging.warning(f"LLM JSON for {row_id} had non-boolean 'native' field: {parsed_json['native']}")
                      return 'unknown', 0, f"LLM JSON had non-boolean 'native' field: {cleaned_response}"
                 llm_reason = parsed_json.get('metadata', 'N/A')
                 reason = f"{'Native' if is_native else 'Non-Native'}. {llm_reason}"
                 logging.info(f"LLM Parsed Result for {row_id}: {classification}")
                 return classification, 100, reason
            else:
                 logging.warning(f"LLM JSON for {row_id} lacks required fields: {cleaned_response}")
                 return 'unknown', 0, f"LLM JSON missing fields: {cleaned_response}"
        except json.JSONDecodeError as e:
             logging.error(f"LLM JSON parsing error for {row_id}: {e}\nRaw response: {cleaned_response}")
             return 'error', 0, f"LLM JSON parsing error: {e}. Response: {cleaned_response}"

    except Exception as e:
        logging.error(f"Error during LLM API call for {row_id}: {e}")
        if response_log_file:
             try:
                 response_log_file.write(f"LLM ERROR for ID: {row_id} \nAPI Error: {e}\n\n")
                 response_log_file.flush()
             except IOError as io_e: logging.warning(f"Could not write LLM error for {row_id}: {io_e}")
        return 'error', 0, f"LLM API Error: {e}"


def write_classified_tables(classification_details, input_df, native_output_path, non_native_output_path):
    """
    Az eredeti metaadat sorokat külön csak natív és nem-natív sorokat tartalmazó fájlokba írja a végső osztályozás
    alapján. A hibás vagy valamilyen okból nem klasszifikált sorok is a nem natívba kerülnek.
    TODO: külön fájlba írni a hibás sorokat

    Argumentumok:
        results (list): List of dictionaries from process_metadata.
        input_df (str): Path to the original input TSV/CSV file.
        native_output_path (str): Path to write the native classified rows.
        non_native_output_path (str): Path to write the non-native classified rows.
    """
    native_ids = set()
    non_native_ids = set()

    for result in classification_details:
        if result['final_classification'] == 'native':
            native_ids.add(result['ID'])
        else:
            non_native_ids.add(result['ID'])

    logging.info(f"Total Native IDs: {len(native_ids)}")
    logging.info(f"Total Non-Native IDs: {len(non_native_ids)}")

    delimiter = '\t'

    written_native = 0
    written_non_native = 0

    with open(native_output_path, "w", encoding="utf-8", newline='') as native_output, \
            open(non_native_output_path, "w", encoding="utf-8", newline='') as non_native_output:

        header = delimiter.join(input_df.columns) + '\n'
        native_output.write(header)
        non_native_output.write(header)


        for index, row in input_df.iterrows():
            current_id = str(row["ID"]).strip()
            line_to_write = delimiter.join(map(str, row.tolist())) + '\n'
            if current_id in native_ids:
                native_output.write(line_to_write)
                written_native += 1
            elif current_id in non_native_ids:
                non_native_output.write(line_to_write)
                written_non_native += 1
            else:
                non_native_output.write(line_to_write)
                written_non_native += 1

    logging.info(f"Finished writing tables: {native_output_path} ({written_native} rows) and {non_native_output_path} ({written_non_native} rows)")