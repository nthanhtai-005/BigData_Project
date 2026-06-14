====================================================================
 BO FILE: 4 MAPREDUCE BANG APACHE PIG  (phan viec cua Huy)
====================================================================

NEN DOC THEO THU TU:
  1. HUONG_DAN_CHAY_PIG.md   <-- HUONG DAN CHINH (tu A->Z, ca buoc gui file + sua loi)
  2. DE_TAI_MAPREDUCE_PIG.md <-- Mo ta 4 de tai (2 de tai cu + 2 de tai MOI)

THU MUC pig_scripts/ :
  - 01_price_gap.pig        (De tai 7 - da co - FILTER/FOREACH/GROUP/AVG)
  - 02_discount_bucket.pig  (De tai 8 - da co - bincond/GROUP/AVG/COUNT)
  - 03_category_scale.pig   (De tai 9 - MOI  - GROUP/COUNT/SUM)
  - 04_price_range.pig      (De tai 10 - MOI - GROUP/MIN/MAX/AVG)
  - run_all.sh              (chay ca 4 bai bang 1 lenh: bash run_all.sh)

FILE DU PHONG:
  - ALL_PIG_SCRIPTS_COPY_PASTE.txt  (go tay/dan tay khi khong chuyen duoc file)

LUU Y QUAN TRONG:
  - Tat ca doc du lieu TU HDFS: /data/bigdata_ecommerce/mapreduce_input/
    (= du lieu cua bang Hive 'mapreduce_input_tsv'), KHONG doc file csv may ca nhan.
  - "Hasaki" va "Lam Thao" la 2 SAN (cot source_name = hasaki / lamthao),
    KHONG phai brand_name.
====================================================================
