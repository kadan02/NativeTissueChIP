# Az osztályozási eredmények statisztikai értékelését végző funciton.

import pandas as pd
import logging
import os
import sys
import datetime
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)
import classification_config as config


# Konfiguráció
BENCHMARK_FILE = config.BENCHMARK_PATH
run_name = "mouse_biomedical"
RESULTS_FILE = "../data/processed/classification/" + run_name + "/classification_summary.csv"
OUTPUT_PREFIX = "../results/benchmarks/" + run_name

# Log fájl útvonalának beállítása az output prefix alapján
if OUTPUT_PREFIX:
    log_dir = os.path.dirname(OUTPUT_PREFIX)
    log_filename_base = os.path.basename(OUTPUT_PREFIX)
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{log_filename_base}_evaluation.log")
else:
    log_dir = "../logs/evaluation"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"evaluation_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

#logging setup
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

def evaluate_classification(benchmark_file, results_file, save_misclass=True):
    """
    Az értékelést elvégző function. Bemenet a jelölt adatokat tartalmazó file és a hibrid/csak-LLM osztályozás eredményeit tartalmazó fájl.

    benchmark_file (str): Útvonal a benchmark adatokhoz (TSV).
    results_file (str): Útvonal az osztályozás eredményekhez (classification_summary.csv).
    save_misclass (bool): Ha True, menti a félre osztályozott sorokat.   """

    # Adatok előkészítése az összehasonlításhoz
    benchmark_df = pd.read_csv(benchmark_file, sep='\t', dtype={"ID": str})
    results_df = pd.read_csv(results_file, dtype={"ID": str})
    benchmark_df["Is_Native"] = benchmark_df["Is_Native"].astype(int)
    prediction_map = {'native': 1, 'non-native': 0}
    results_df['prediction_numeric'] = results_df['final_classification'].map(prediction_map).fillna(-1).astype(int)

    # Két dataframe összevonása az 'ID' oszlop alapján
    merged_df = pd.merge(benchmark_df, results_df, on='ID', how='inner')
    logging.info(f"Merged {len(merged_df)} rows based on matching IDs.")

    valid_predictions_mask = merged_df['prediction_numeric'].isin([0, 1])
    y_true = merged_df["Is_Native"][valid_predictions_mask]
    y_pred = merged_df['prediction_numeric'][valid_predictions_mask]

    # Innentől statisztikák számítása

    # Általános pontosság az összes mintán
    accuracy = accuracy_score(y_true, y_pred)
    logging.info(f"Overall Accuracy: {accuracy:.4f}")

    # Natív osztály statisztikái
    precision_native, recall_native, f1_native, _ = precision_recall_fscore_support(
        y_true, y_pred, average='binary', pos_label=1, zero_division=0
    )
    # Nem-natív osztály statisztikái
    precision_nonnative, recall_nonnative, f1_nonnative, _ = precision_recall_fscore_support(
        y_true, y_pred, average='binary', pos_label=0, zero_division=0
    )

    # Teljes statisztikai jelentés (osztályonkénti statisztikák és átlagok)
    report = classification_report(y_true, y_pred, target_names=['Non-Native (0)', 'Native (1)'], zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

    logging.info(f"\nMetrics for 'Native' class (Positive Label = 1):")
    logging.info(f"  Precision: {precision_native:.4f}")
    logging.info(f"  Recall:    {recall_native:.4f}")
    logging.info(f"  F1-Score:  {f1_native:.4f}")

    logging.info(f"\nMetrics for 'Non-Native' class (Positive Label = 0):")
    logging.info(f"  Precision: {precision_nonnative:.4f}")
    logging.info(f"  Recall:    {recall_nonnative:.4f}")
    logging.info(f"  F1-Score:  {f1_nonnative:.4f}")
    logging.info("\nConfusion Matrix ([0, 1] labels):")
    logging.info("            Predicted 0  Predicted 1")
    logging.info(f"Actual 0    {cm[0][0]:^11d}  {cm[0][1]:^11d}")
    logging.info(f"Actual 1    {cm[1][0]:^11d}  {cm[1][1]:^11d}")
    logging.info("  (TN, FP)")
    logging.info("  (FN, TP)")
    logging.info("\nFull Classification Report:")
    for line in report.split('\n'):
        logging.info(line)


    # Azok a sorok azonosítása, ahol a predikció nem egyezett a manuális jelöléssel
    merged_df['is_correct'] = (merged_df["Is_Native"] == merged_df['prediction_numeric'])
    misclassified_df = merged_df[~merged_df['is_correct']].copy()
    logging.info(f"\nTotal Misclassified Samples: {len(misclassified_df)}")

    # Félre azonosított adatok mentése új fájlba
    if save_misclass:
        error_file_path = f"{OUTPUT_PREFIX}_misclassified.csv"
        columns_to_save = [
            'ID',
            "Is_Native",
            'final_classification',
            'classification_method',
            'keyword_reason',
            'llm_reason'
        ]
        misclassified_df[columns_to_save].to_csv(error_file_path, index=False)
        print(f"\nMisclassified samples saved to: {error_file_path}")

    elif save_misclass and misclassified_df.empty:
        print("\nNo misclassified samples found.")


evaluate_classification(BENCHMARK_FILE,RESULTS_FILE)