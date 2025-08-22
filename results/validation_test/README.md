### BED fájlok Jaccard-index hasonlósági tesztelése

A vizsgálandó kérdés, hogy az osztályozással előállított *natív* csoport jelentősen magasabb homogenitást mutat-e, mint az azonos méretű, de véletlenszerűen összeállított csoportok, amelyek a *nem-natív* kisérletek adatait is tartalmazhatják.

### A vizsgálat módszere röviden
**A [run_test.py](https://github.com/kadan02/NativeTissueChIP/blob/master/results/validation_test/run_test.py) a következőeket végzi el:**
1. A bedtools csomag [jaccard](https://bedtools.readthedocs.io/en/latest/content/tools/jaccard.html) parancsát felhasználva kiszámítja az atlagos páronkénti hasonlóságot a „natív” csoporton belül.
2. Felhasználva a nem-natív adatsorokat is, elvégez N iterációt véletlenszerű mintavétellel és kiszámítja az átlagos páronkénti Jaccard-indexszet ezekben a csoportokban is.
3. Kiszámítja a p-értéket azáltal, hogy összehasonlítja a natív csoport átlagos hasonlóságát a véletlenszerű minták átlagainak eloszlásával.

*A vizsgálandó natív és nem natív csoportokat esetemben úgy állítottam össze, hogy azonos transzkripciós faktort vizsgáljanak, és a szövet- és sejttípus minél inkább megegyezzen.*

## Használat
A script két fő bemeneti fájlt igényel, amelyeket a `config.yaml` fájlban kell megadni:

1.  **Natív BED Fájl (`native_bed_file`):** A "natív" kategóriába sorolt kísérletek peakjeit tartalmazza.
2.  **Nem-natív BED Fájl (`non_native_bed_file`):** A "nem-natív" kategóriába sorolt kísérletek peakjeit tartalmazza.

### BED Fájl Formátuma
A 4. oszlop (ID) formátuma kritikus:

`SRX_AZONOSÍTÓ_csúcs_száma`

Például:
```
chr1	631957	632259	SRX018991_0000001	TP63
```

A BED fájlok létrehozhatóak a [filter_beds.py](https://github.com/kadan02/NativeTissueChIP/blob/master/scripts/filter_beds.py) scripttel.

### Konfiguráció

A paramétereket a `config.yaml` fájlban kell megadni.

### Futtatás

A szkript futtatása a terminálból:

```bash
python jaccard_validation.py --config config.yaml
```
