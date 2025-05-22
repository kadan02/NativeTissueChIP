# TFLink 2.0 szövetspecifikus ChIP-seq Pipeline

#### Ez a repository a szövet- és szervspecifikus ChIP-Seq adatok feldolgozására szolgáló scriptek gyűjteménye a [TFLink](https://tflink.net/) adatbázis bővítésének részeként.
## A scriptek fő funkciói:
- ### Metaadatok előfeldolgozása és szűrése
   - Nagy méretű metaadat-táblázatok formázása és szűrése kulcsszavak/kifejezések alapján
   - Kísérleti minták minőségi ellenőrzése: natív és manipulált minták elkülönítése Large Language Model (LLM) alapú szűrés segítségével
- ### BED fájlok feldolgozása
   - Transzkripciós faktor kötőhelyek szekvenciáinak előállítása
   - Traszkripciós faktor - Target gén interakciók azonosítása és táblázatok formázása Uniprot és NCBI keresztlinkekkel

# Fontos fájlok elérhetőségei:
- [Osztályozási futtatások nyers adatai](https://github.com/kadan02/NativeTissueChIP/tree/master/data/processed/classification) (lásd README fájl a linken belül extra magyarázatért)
- [Osztályozási futtatások benchmark eredményei](https://github.com/kadan02/NativeTissueChIP/tree/master/results/benchmarks)
- [Kulcsszavak listái](https://github.com/kadan02/NativeTissueChIP/tree/master/data/raw/cell_lines)
- [Jelölt humán adathalmaz](https://github.com/kadan02/NativeTissueChIP/blob/master/data/processed/metadata/labeled_data.tsv)
# A pipeline futtatásához instrukciók [itt](https://github.com/kadan02/NativeTissueChIP/wiki) találhatóak.
# Credits
This project was made possible using data from [ChIP-Atlas](https://chip-atlas.org).
1. Zou, Z., Ohta, T., Oki, S. ChIP-Atlas 3.0: a data-mining suite to explore chromosome architecture together with large-scale regulome data. Nucleic Acids Res. 52(W1), W45-W53, 2024. [http://dx.doi.org/10.1093/nar/gkae358](http://dx.doi.org/10.1093/nar/gkae358)
2. Zou, Z., Ohta, T., Miura, F., Oki, S. ChIP-Atlas 2021 update: a data-mining suite for exploring epigenomic landscapes by fully integrating ChIP-seq, ATAC-seq and Bisulfite-seq data. Nucleic Acids Res. 50(W1), W175-W182, 2022. [http://dx.doi.org/10.1093/nar/gkac199](http://dx.doi.org/10.1093/nar/gkac199)
3. Oki, S., Ohta, T., Shioi, G., Hatanaka, H., Ogasawara, O., Okuda, Y., Kawaji, H., Nakaki, R., Sese, J., Meno, C. ChIP-Atlas: a data-mining suite powered by full integration of public ChIP-seq data. EMBO Rep. 19(12), e46255, 2018. [http://dx.doi.org/10.15252/embr.201846255](http://dx.doi.org/10.15252/embr.201846255)
4. Web Tool: Oki, S; Ohta, T (2015): ChIP-Atlas. [https://chip-atlas.org](https://chip-atlas.org)

