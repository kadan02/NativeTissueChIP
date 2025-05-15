# A classification_main.py konfigurációit ebben a fájlban kell megadni.

import os
from dotenv import load_dotenv

# Fájl útvonalak
INPUT_METADATA_PATH = "../data/processed/metadata/mouse_preprocessed.tsv"
BENCHMARK_PATH = "../data/processed/metadata/mouse_labeled.tsv"
BASE_OUTPUT_DIR = "../data/processed/classification"

# LLM konfiguráció
load_dotenv("../api_variables.env")
LLM_SERVER_URL = os.getenv("LLM_SERVER_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")

# System prompt
LLM_INSTRUCTIONS ="""
# Role
You are an expert cellular biologist specialized in classifying biological samples. Your responses must be precise and adhere strictly to the requested format.

# Task Overview
Your task is to classify the sequencing sample described in the user's message as either NATIVE or NON-NATIVE. The user will provide the data as a single line containing the sample ID followed by its associated metadata.

# Definitions
### Native Samples
- **Normal Physiological Conditions**: Mimic normal, resting physiological conditions.
- **Healthy Specimens**: Come from healthy, unmodified, and drug-free specimens.
- **Wild-Type (WT)**, Untreated, Control and Vehicle samples are usually native.
- **DMSO** is usually used in control experiments so it is **not non-native**.

### Non-Native Samples
- **Immortalized Cell Lines**: The metadata can contain an immortalized cell line name (e.g., HeLa, HEK293, C20). Mention of a generic human cell type (e.g., 'T cells', 'fibroblasts') or primary cell line is NOT a non-native indicator unless modified.
- **Embyrionic cells**: including keywords such as 'fetal', 'embryonic'.
- **Modifications**, including:
  - cancer, tumor
  - treated
  - knockout, knockdown, KO, KD
  - Any clear synonyms or abbreviations of these modification terms.
- In the case of donors, specimens with very young (fetal or newborn) age.
- Diseases not affecting the given tissue or organ are not non-native indicators.
- 'Activated' and 'Differentiated' are **NOT non-native** indicators.
- **Mixed Indicators**: If a sample's metadata contains clear indicators for BOTH native and non-native according to these rules, classify it as **non-native**.

# Answer Format
Return only a single, valid JSON object with this structure:
{"id": "<id>", "metadata": "<reason>", "native": <true/false>}

In "<reason>" directly reference the part(s) of the metadata which you drew your conclusions from.

### Answer examples:
{"id": "SRX12345", "metadata": "genotype=wild-type", "native": true}
{"id": "SRX67890", "metadata": "cell_line=C20", "native": false}
{"id": "SRX98765", "metadata": "genotype=MED12-KO", "native": false}
"""

# A kulcsszavakat itt adjuk meg, amelyekhez súlyokat is rendelünk. Nagyobb súly = magasabb konfidencia érték az eredménynél
KEYWORD_CATEGORIES = {
    'strong_non_native': {
        'keywords': ["knockout", "ko", "kd", "knockdown" "transformed","immortalized", "overexpression","cancer",
                     "tumor","fetal", "embryonic","RNAi", "cell line", "neonatal","treated","treatment","leukemic",
                     "leukemia","shRNA","drug","null","inhibited","stimulated"],
        'weight': 95,
        'classification': 'non-native'
    },
    'weak_non_native': {
        'keywords': ["induced"],
        'weight': 50,
        'classification': 'non-native'
    },

    'weak_native': {
        'keywords': ["donor","wild type", "wt", "control", "vehicle", "untreated","normal",
                     "wt","wild-type","unstimulated","DMSO", "no treatment"],
        'weight': 50,
        'classification': 'native'
    },
    'strong_native': {
        'keywords': ["biopsy","healthy donor"],
        'weight': 75,
        'classification': 'native'
    }
}

# Egyéb változók
FUZZY_THRESHOLD = 75    # a határérték, ami alatt 2 string nem egyezik meg
FUZZY_MAX_LEN = 2       # max hosszúságú egymást követő szavak, amiket összehasonlítunk