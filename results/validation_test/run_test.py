#!/usr/bin/env python3

import argparse
import itertools
import random
import subprocess
import sys
import tempfile
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import yaml


def load_config(config_path: Path) -> Dict[str, Any]:
    """Betölti a YAML konfigurációs fájlt."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def read_bed_as_df(path: Path) -> pd.DataFrame:
    """
    Beolvas egy BED fájlt egy DataFrame-be, és kinyeri az SRX azonosítókat.
    """
    col_names = ["chrom", "start", "end", "id", "tf"]
    df = pd.read_csv(
        path, sep="\t", header=None, names=col_names, usecols=range(5),
        dtype={"chrom": str, "start": int, "end": int, "id": str, "tf": str}, comment="#",
    )
    df["SRX_ID"] = df["id"].astype(str).str.split("_", n=1).str[0]
    return df


def load_data_and_derive_ids(
        native_bed_path: Path, non_native_bed_path: Path
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Betölti a natív és nem-natív BED fájlokat és visszaadja az egyesített DataFrame-et, valamint a natív SRX azonosítók listáját.
    """
    print(f"Natív csúcsok betöltése: {native_bed_path}")
    native_df = read_bed_as_df(native_bed_path)
    if native_df.empty:
        raise ValueError(f"A natív BED fájl üres vagy nem tölthető be: {native_bed_path}")

    print(f"Nem-natív csúcsok betöltése: {non_native_bed_path}")
    non_native_df = read_bed_as_df(non_native_bed_path)

    native_ids = sorted(list(native_df["SRX_ID"].unique()))
    print(f"{len(native_ids)} egyedi SRX azonosító a natív csoportban.")

    combined_df = pd.concat([native_df, non_native_df], ignore_index=True)
    print(f"Összesen {len(combined_df)} csúcs betöltve {combined_df['SRX_ID'].nunique()} egyedi SRX azonosítótól.")
    return combined_df, native_ids


def _write_tmp_bed(df: pd.DataFrame) -> Path:
    """Egy DataFrame tartalmát kiírja egy ideiglenes BED fájlba a bedtools számára."""
    tmp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".bed", newline="")
    df.to_csv(tmp_file.name, sep="\t", header=False, index=False, columns=["chrom", "start", "end"])
    tmp_file.close()
    return Path(tmp_file.name)


def parse_bedtools_jaccard_output(stdout: str) -> Optional[float]:
    """Értelmezi a 'bedtools jaccard' parancs kimenetét és kinyeri a Jaccard-indexet."""
    if not stdout: return None
    lines = [l for l in stdout.strip().splitlines() if l and not l.startswith("#")]
    if not lines: return None
    parts = lines[-1].strip().split()
    if len(parts) >= 3:
        try:
            return float(parts[2])
        except (ValueError, IndexError):
            return None
    return None


def jaccard_between_srx(srx_a_df: pd.DataFrame, srx_b_df: pd.DataFrame) -> Optional[float]:
    """Kiszámítja a Jaccard-indexet két, DataFrame-ben tárolt csúcshalmaz között a bedtools segítségével."""
    a_tmp_path, b_tmp_path = _write_tmp_bed(srx_a_df), _write_tmp_bed(srx_b_df)
    try:
        cmd = ["bedtools", "jaccard", "-a", str(a_tmp_path), "-b", str(b_tmp_path)]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            print(f"Hiba a bedtools futtatása közben:\n{proc.stderr}", file=sys.stderr)
            return None
        return parse_bedtools_jaccard_output(proc.stdout)
    finally:
        # Ideiglenes fájlok törlése
        for p in (a_tmp_path, b_tmp_path):
            if p.exists():
                p.unlink()


def mean_pairwise_jaccard(srx_ids: Iterable[str], universe_df: pd.DataFrame) -> float:
    """Kiszámítja az átlagos páronkénti Jaccard-hasonlóságot egy adott SRX azonosító listára."""
    ids = list(srx_ids)

    scores: List[float] = []
    for id_a, id_b in itertools.combinations(ids, 2):
        df_a = universe_df.loc[universe_df["SRX_ID"] == id_a, ["chrom", "start", "end"]].sort_values(by=["chrom", "start"])
        df_b = universe_df.loc[universe_df["SRX_ID"] == id_b, ["chrom", "start", "end"]].sort_values(by=["chrom", "start"])

        if df_a.empty or df_b.empty:
            continue

        jaccard_score = jaccard_between_srx(df_a, df_b)
        if jaccard_score is not None:
            scores.append(jaccard_score)

    return mean(scores) if scores else 0.0


def plot_distribution(native_mean: float, random_means: List[float], p_value: float, out_path: Path) -> None:
    """Legenerálja és elmenti az eredményeket bemutató disztribúciós ábrát."""
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(random_means, kde=True, stat="density", ax=ax, label="Véletlen minták átlagai")
    ax.axvline(native_mean, color="red", linestyle="--", linewidth=2, label=f"Natív csoport átlaga ({native_mean:.4f})")
    ax.set_title("A 'natív' klasszifikáció validálása véletlen mintavétellel szemben", fontsize=14)
    ax.set_xlabel("Átlagos páronkénti Jaccard-index")
    ax.set_ylabel("Sűrűség")
    ax.legend()
    ax.text(0.95, 0.6, f"p-érték: {p_value:.4f}", transform=ax.transAxes, fontsize=12,
            verticalalignment='center', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f"Ábra elmentve ide: {out_path}")


def main() -> int:
    """Fő program és CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=Path, required=True)
    args = parser.parse_args()

    config = load_config(args.config)

    seed = config.get("seed")
    if seed is not None:
        random.seed(seed)
        print(f"seed: {seed}")

    native_bed = Path(config["native_bed_file"])
    non_native_bed = Path(config["non_native_bed_file"])
    df, native_ids = load_data_and_derive_ids(native_bed, non_native_bed)

    all_srx_pool = sorted(list(df["SRX_ID"].unique()))

    k = len(native_ids)

    print(f"A natív csoport átlagos Jaccard-indexének számítása (k={k})...")
    native_mean = mean_pairwise_jaccard(native_ids, df)
    print(f"Natív csoport átlagos Jaccard-index: {native_mean:.6f}")

    iterations = config["iterations"]
    random_means: List[float] = []
    for i in range(iterations):
        sample_ids = random.sample(all_srx_pool, k)
        random_means.append(mean_pairwise_jaccard(sample_ids, df))
        if (i + 1) % max(1, iterations // 10) == 0:
            print(f"Iteráció: {i + 1}/{iterations}...")

    more_extreme_count = sum(1 for x in random_means if x >= native_mean)
    p_value = (more_extreme_count + 1) / (len(random_means) + 1)
    print(f"p-érték = {p_value:.6f}")

    plot_distribution(native_mean, random_means, p_value, Path(config["output_plot"]))

    return 0

if __name__ == "__main__":
    sys.exit(main())