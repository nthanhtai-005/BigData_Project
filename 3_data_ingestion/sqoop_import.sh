#!/bin/bash

MYSQL_HOST="192.168.100.1"       # IP Windows
MYSQL_PORT="3306"
MYSQL_DB="bigdata_ecommerce"
MYSQL_USER="root"
MYSQL_PASS="MatKhauCuaBan"       # Cap nhat mat khau tai day
HIVE_DB="bigdata_ecommerce"

echo "HUT DU LIEU TU MYSQL SANG HIVE STAGING BANG SQOOP..."

BANG_CAN_HUT=("sources" "categories" "brands" "products")

for BANG in "${BANG_CAN_HUT[@]}"
do
  echo "Dang import bang: $BANG ..."
  sqoop import \
    --connect "jdbc:mysql://${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DB}?useSSL=false" \
    --username "${MYSQL_USER}" \
    --password "${MYSQL_PASS}" \
    --table "$BANG" \
    --hive-import \
    --hive-overwrite \
    --hive-table "${HIVE_DB}.staging_${BANG}" \
    -m 1
done

echo "CHUYEN DU LIEU SANG PARQUET VA TAO BANG PHANG..."

hive -e "
USE ${HIVE_DB};
SET hive.exec.dynamic.partition = true;
SET hive.exec.dynamic.partition.mode = nonstrict;

-- Nap 3 bang danh muc
INSERT OVERWRITE TABLE sources SELECT * FROM staging_sources;
INSERT OVERWRITE TABLE categories SELECT * FROM staging_categories;
INSERT OVERWRITE TABLE brands SELECT * FROM staging_brands;

-- Nap bang phan vung
INSERT OVERWRITE TABLE final_products PARTITION (category_id)
SELECT id, source_id, brand_id, name, num_images, price, market_price, 
       discount_amount, discount_percent, has_discount, sold_count, stock_quantity, 
       scraped_at, category_id 
FROM staging_products;

-- Nap bang phang cho MapReduce
INSERT OVERWRITE TABLE flat_products_for_mapreduce
SELECT p.id, p.name, s.source_name, c.category_name, b.brand_name, p.price, p.discount_percent, p.sold_count
FROM final_products p
JOIN sources s ON p.source_id = s.id
JOIN categories c ON p.category_id = c.id
JOIN brands b ON p.brand_id = b.id;
"

echo "HOAN TAT TOAN BO QUA TRINH ETL! HE THONG DA SAN SANG PHAN TICH."