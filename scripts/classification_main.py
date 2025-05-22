# A hibrid/csak LLM osztályozást vezérlő main script.

import pandas as pd
import os
import sys
import logging
from datetime import datetime
from openai import OpenAI
import classification_config as config
import classification_utils as utils

# Ha True, akkor a kulcsszavas keresések ki lesznek hagyva és csak az LLM lesz meghívva
llm_only_mode = False


def process_metadata(df, llm_only, llm_client=None, llm_model_name=None, prompt_output=None, llm_response_log_file=None):
    """
    A metaadat táblázaton soronként iterál. Az osztályozás menete:
        1. Először megpróbál kulcsszavak alapján osztályzni.
        2. Ha nem-natív indikátor kulcsszavat talál, következő sor.
        3. Ha natív indikátor kulcsszavat talál, LLM-el validálás. Ha ellenkező eredmény jön ki, akkor
        erről figyelmeztetés lesz a logfájlban.
        4. Ha semmilyen kulcsszavat nem talál, akkor LLM meghívás, és következő sor.

        Ha llm_only=True, akkor csak LLM meghívás.

    Argumentumok:
        df (str): A metaadat táblázat DataFrame-vé alakítva.
        llm_client (str): A LLM-et futtató szerver URL-je.
        llm_model_name (str): Modell neve (pl. mistral-small:24b)
        prompt_output (str): Útvonal, ahova a system és user prompt írásra kerül.
        llm_response_log_file (str): Az útvonal, ahove az LLM "nyers" válaszai írásra kerülnek.

    Return:
        classification_details (dict) a következő kulcsokkal:
            'ID'
            'keyword_classification'
            'keyword_confidence'
            'keyword_reason'
            'llm_classification'
            'llm_reason'
            'classification_method'
    """

    classification_details = []

    logging.info(f"Starting processing of {len(df)} rows.  LLM-Only mode: {llm_only}")

    for i, row in df.iterrows():
        row_id = str(row["ID"])
        logging.info(f"Processing row {i + 1}/{len(df)}, ID: {row_id}")

        # 1. Kulcsszavas osztályozás
        if not llm_only:
            cleaned_keywords = utils.clean_keywords(config.KEYWORD_CATEGORIES)
            metadata = str(row["Metadata"]) if pd.notna(row["Metadata"]) else ""

        # A "nincs találat" eset inicializilása
        kw_class = 'skipped' if llm_only else 'unknown'
        kw_conf = 0
        kw_reason = "Keyword search skipped (LLM-Only mode)" if llm_only else "No relevant keywords"
        method = 'LLM' if llm_only else 'Keyword (Initial)'

        if not llm_only:
            if not metadata.strip():
                kw_reason = f"Metadata column empty"
                kw_class = 'unknown'
            else:
                extracted_pairs = utils.extract_key_value_pairs(metadata)
                if extracted_pairs:
                    keyword_matches = utils.find_keywords(cleaned_keywords, extracted_pairs, threshold=config.FUZZY_THRESHOLD, max_len=config.FUZZY_MAX_LEN)
                    if keyword_matches:
                        kw_class, kw_conf, kw_reason = utils.classify_based_on_keywords(keyword_matches)
                        match_details = [f"'{m['keyword']}' in '{m['source_key']}' ({m['category']}/{m['score']})" for m in keyword_matches]
                        kw_reason += f". Matches found: {'; '.join(match_details)}"
                else:
                    kw_reason = "No key=value pairs found"
                    kw_class = 'unknown'

            logging.info(f"Row {i + 1} (ID: {row_id}): Keyword analysis - Initial Class: {kw_class}, Conf: {kw_conf}, Reason: {kw_reason}")

        # 2. LLM meghívás
        # Először a DataFrame-et formázzuk az LLM-nek megfelelő formába
        llm_input_parts = []
        for col in df.columns:
            # Transzkripciós faktor oszlopot nem küldjük el az LLM-nek (nem releváns, csak a tokeneket növelné)
            if col == 'Transcription_Factor': continue
            if pd.notna(row[col]):
                 llm_input_parts.append(f"{col}={str(row[col])}")
        llm_combined_text = " | ".join(llm_input_parts)
        llm_text_for_api = f"{row_id}\t{llm_combined_text}" # This is the data payload for the user prompt

        # Inicializálás
        final_classification = kw_class
        llm_reason = ''

        if not llm_only and kw_class == 'non-native':
            method = 'Keyword (Non-Native)'
        elif not llm_only and kw_class != 'skipped':
            method = f'Keyword ({kw_class})'

        # LLM futtatása, ha a kulcsszavas megoldás nem megbízható
        if (llm_only or kw_class in ['unknown', 'ambiguous', 'native']) and llm_client and llm_model_name:
            if llm_only:
                logging.info(f"Row {i + 1} (ID: {row_id}): LLM-Only mode. Calling LLM.")
                method = 'LLM'
            elif kw_class == 'native':
                logging.info(f"Row {i + 1} (ID: {row_id}): Keyword classification 'native'. Validating with LLM.")
                method = 'LLM (Native Validation)'
            else:
                logging.info(f"Row {i + 1} (ID: {row_id}): Keyword classification inconclusive ('{kw_class}'). Attempting LLM fallback.")
                method = 'LLM (Fallback)'

            llm_class, llm_conf, llm_reason_text = utils.classify_with_llm(
                row_id,
                llm_text_for_api,
                llm_client,
                llm_model_name,
                prompt_output,
                response_log_file=llm_response_log_file
            )
            llm_reason = llm_reason_text

            if llm_class in ['native', 'non-native']:
                final_classification = llm_class
                logging.info(f"Row {i + 1} (ID: {row_id}): LLM classified as '{llm_class}'. Using LLM result.")
                if not llm_only and kw_class == 'native' and llm_class == 'non-native':
                    logging.warning(f"Row {i + 1} (ID: {row_id}): LLM OVERRIDE: Keyword was 'native', LLM classified as 'non-native'.")
            elif llm_class == 'error':
                 logging.error(f"Row {i + 1} (ID: {row_id}): LLM classification failed. Reverting to keyword result: '{kw_class}'")
                 final_classification = 'error' if llm_only else kw_class
                 method = f'Keyword ({kw_class} / LLM Error)'
            else:
                 logging.warning(f"Row {i + 1} (ID: {row_id}): LLM also returned '{llm_class}'. Reverting to keyword result: '{kw_class}'")
                 final_classification = 'unknown' if llm_only else kw_class
                 method += ' / LLM Unknown'

        elif kw_class == 'non-native':
             logging.info(f"Row {i + 1} (ID: {row_id}): Keyword classification is 'non-native'. Skipping LLM.")
             method = 'Keyword (Non-Native)'

        classification_details.append({
            'ID': row_id,
            'keyword_classification': kw_class,
            'keyword_confidence': kw_conf,
            'keyword_reason': kw_reason,
            'final_classification': final_classification,
            'llm_reason': llm_reason,
            'classification_method': method
        })

    return classification_details


if __name__ == "__main__":

    INPUT_METADATA_PATH = config.INPUT_METADATA_PATH
    run_name_arg = input(f"Enter output directory name (Leave empty for timestamp, default base: '{config.BASE_OUTPUT_DIR}'): ")

    # A futtatás (output mappa) neve. Ha üres input, akkor dátum
    run_name = run_name_arg if run_name_arg else datetime.now().strftime("%Y%m%d_%H%M%S")
    output_run_dir = os.path.join(config.BASE_OUTPUT_DIR, run_name)
    try:
        os.makedirs(output_run_dir, exist_ok=True)
        print(f"Using output directory: '{output_run_dir}'")
    except Exception as e:
        print(f"Error creating directory '{output_run_dir}': {e}. Exiting.", file=sys.stderr)
        sys.exit(1)

    # Logging setup
    log_file = os.path.join(output_run_dir, "classification_run.log")
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)-8s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename=log_file,
                        filemode='w')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(message)s', datefmt='%H:%M:%S')
    console_handler.setFormatter(console_formatter)
    logging.getLogger('').addHandler(console_handler)

    logging.info(f"Script started. Output directory: {output_run_dir}")
    logging.info(f"Full log file: {log_file}")

    # Benchmark mód. Ez egy külön táblázatot használ, amelynek első oszlopja az ID, második hogy natív/nem natív (0 vagy 1)
    BENCHMARK_FILE_PATH = None
    run_mode = input("Run in benchmark mode? (y/n): ").lower().strip()
    if run_mode == 'y':
        print("\nBenchmark mode selected.")
        BENCHMARK_FILE_PATH = config.BENCHMARK_PATH
        logging.info(f"Processing benchmark file: {BENCHMARK_FILE_PATH})")
    elif run_mode == 'n':
        logging.info("Processing full dataset.")
    else:
        print("Invalid input. Please enter 'y' or 'n'.")

    # Output fájlnevek
    results_summary_path = os.path.join(output_run_dir, "classification_summary.csv")
    llm_prompt_path = os.path.join(output_run_dir, "llm_last_prompt.txt")
    native_table_path = os.path.join(output_run_dir, "native_classified.tsv")
    non_native_table_path = os.path.join(output_run_dir, "non_native_classified.tsv")
    llm_response_log_path = os.path.join(output_run_dir, "llm_responses.log")


    # LLM kliens inicializálása
    llm_client = None
    if config.LLM_SERVER_URL and config.LLM_API_KEY and "PLACEHOLDER" not in config.LLM_API_KEY:
        try:
            llm_client = OpenAI(base_url=config.LLM_SERVER_URL, api_key=config.LLM_API_KEY)
            logging.info(f"LLM Client initialized. URL: {config.LLM_SERVER_URL}, Model: {config.LLM_MODEL_NAME})")
        except Exception as e:
             logging.error(f"Failed to initialize LLM client: {e}")
    else:
        logging.warning("LLM API URL or Key not set. LLM disabled.")


    # Metaadat betölése
    logging.info(f"Loading metadata from: {INPUT_METADATA_PATH}")
    benchmark_ids = None
    try:
        # Benchmark metaadat táblázat
        if BENCHMARK_FILE_PATH:
            logging.info(f"Loading benchmark IDs from: {BENCHMARK_FILE_PATH}")
            benchmark_df_ids = pd.read_csv(BENCHMARK_FILE_PATH, sep='\t', usecols=["ID"])
            benchmark_ids = set(benchmark_df_ids["ID"].unique())
            logging.info(f"Loaded {len(benchmark_ids)} unique IDs from benchmark file.")

        # Main metaadat táblázat
        metadata_df = pd.read_csv(INPUT_METADATA_PATH, sep="\t", dtype=str, keep_default_na=False)
        logging.info(f"Loaded {len(metadata_df)} rows and {len(metadata_df.columns)} columns.")

        # Ha benchmark, akkor az ID-k matchelése a két táblázat között
        if benchmark_ids:
            initial_rows = len(metadata_df)
            metadata_df = metadata_df[metadata_df["ID"].isin(benchmark_ids)].copy()
            filtered_rows = len(metadata_df)
            logging.info(f"Filtered main metadata to {filtered_rows} rows based on benchmark IDs (from {initial_rows} initial rows).")


    except Exception as e:
        logging.error(f"Failed to load or parse metadata: {e}")
        sys.exit(1)

    # Function meghívása
    logging.info("Starting metadata classification process...")

    with open(llm_response_log_path, 'a', encoding='utf-8') as llm_log_file:
        classification_details = process_metadata(
            metadata_df,
            llm_only_mode,
            llm_client=llm_client,
            llm_model_name=config.LLM_MODEL_NAME,
            prompt_output=llm_prompt_path,
            llm_response_log_file=llm_log_file
            )

    logging.info("Metadata processing finished.")

    # Eredmények mentése
    try:
        summary_df = pd.DataFrame(classification_details)
        summary_df.to_csv(results_summary_path, index=False)
        logging.info(f"Classification summary saved to: {results_summary_path}")
    except Exception as e:
        logging.error(f"Failed to save classification summary: {e}")

    # Új csak natív/nem natív adatokat tartalmazó táblázatok írása
    logging.info("Writing final native/non-native tables...")
    utils.write_classified_tables(
        classification_details,
        metadata_df,
        native_table_path,
        non_native_table_path,)

logging.info("Script finished.")