from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# ============================================================
# MYSQL TREN WINDOWS
# ============================================================
MYSQL_HOST = "192.168.23.1"
MYSQL_PORT = "3306"
MYSQL_DATABASE = "bigdata_ecommerce"
MYSQL_USER = "root"
MYSQL_PASSWORD = "nmt1610104"

# ============================================================
# THU MUC DU LIEU TREN HDFS
# ============================================================
HDFS_BASE = "hdfs:///data/bigdata_ecommerce"


def write_parquet(df, path, partition_column=None):
    writer = df.write.mode("overwrite")

    if partition_column:
        writer = writer.partitionBy(partition_column)

    writer.parquet(path)


def run_etl():
    print("====================================================")
    print("BAT DAU ETL: MYSQL WINDOWS -> HDFS")
    print("====================================================")

    spark = (
        SparkSession.builder
        .appName("E-commerce ETL to HDFS")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    try:
        mysql_url = (
            f"jdbc:mysql://{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
            "?useSSL=false"
            "&allowPublicKeyRetrieval=true"
            "&serverTimezone=UTC"
        )

        mysql_properties = {
            "user": MYSQL_USER,
            "password": MYSQL_PASSWORD,
            "driver": "com.mysql.cj.jdbc.Driver",
        }

        # ----------------------------------------------------
        # 1. DOC DU LIEU MYSQL
        # ----------------------------------------------------
        print("\n[1/5] Doc du lieu tu MySQL Windows...")

        df_sources = spark.read.jdbc(
            url=mysql_url,
            table="sources",
            properties=mysql_properties,
        )

        df_categories = spark.read.jdbc(
            url=mysql_url,
            table="categories",
            properties=mysql_properties,
        )

        df_brands = spark.read.jdbc(
            url=mysql_url,
            table="brands",
            properties=mysql_properties,
        )

        df_products = spark.read.jdbc(
            url=mysql_url,
            table="products",
            properties=mysql_properties,
        )

        print(f"  -> sources:    {df_sources.count()} dong")
        print(f"  -> categories: {df_categories.count()} dong")
        print(f"  -> brands:     {df_brands.count()} dong")
        print(f"  -> products:   {df_products.count()} dong")

        # ----------------------------------------------------
        # 2. GHI CAC BANG GOC LEN HDFS
        # ----------------------------------------------------
        print("\n[2/5] Ghi cac bang Parquet len HDFS...")

        write_parquet(
            df_sources,
            f"{HDFS_BASE}/hive/sources",
        )

        write_parquet(
            df_categories,
            f"{HDFS_BASE}/hive/categories",
        )

        write_parquet(
            df_brands,
            f"{HDFS_BASE}/hive/brands",
        )

        write_parquet(
            df_products,
            f"{HDFS_BASE}/hive/final_products",
            partition_column="category_id",
        )

        print("  -> final_products partition theo category_id")

        # ----------------------------------------------------
        # 3. TAO BANG PHANG
        # ----------------------------------------------------
        print("\n[3/5] Tao bang phang cho Hive va MapReduce...")

        df_flat_products = (
            df_products.alias("p")
            .join(
                df_sources.alias("s"),
                col("p.source_id") == col("s.id"),
                "inner",
            )
            .join(
                df_categories.alias("c"),
                col("p.category_id") == col("c.id"),
                "inner",
            )
            .join(
                df_brands.alias("b"),
                col("p.brand_id") == col("b.id"),
                "inner",
            )
            .select(
                col("p.id").cast("long").alias("id"),
                col("p.name").cast("string").alias("name"),
                col("p.source_id").cast("long").alias("source_id"),
                col("p.brand_id").cast("long").alias("brand_id"),
                col("s.source_name").cast("string").alias("source_name"),
                col("c.category_name").cast("string").alias("category_name"),
                col("b.brand_name").cast("string").alias("brand_name"),
                
                # CAC COT BO SUNG TU MYSQL
                col("p.num_images").cast("long").alias("num_images"),
                col("p.price").cast("double").alias("price"),
                col("p.market_price").cast("double").alias("market_price"),
                col("p.discount_amount").cast("double").alias("discount_amount"),
                col("p.discount_percent").cast("double").alias("discount_percent"),
                col("p.has_discount").cast("integer").alias("has_discount"),
                col("p.sold_count").cast("long").alias("sold_count"),
                col("p.stock_quantity").cast("long").alias("stock_quantity"),
                col("p.scraped_at").cast("string").alias("scraped_at"),
                
                col("p.category_id").cast("long").alias("category_id"),
            )
        )

        total_flat = df_flat_products.count()

        print(f"  -> flat_products: {total_flat} dong")

        # ----------------------------------------------------
        # 4. PARQUET PARTITIONED CHO HIVE
        # ----------------------------------------------------
        print("\n[4/5] Ghi Parquet partitioned cho Hive...")

        write_parquet(
            df_flat_products,
            f"{HDFS_BASE}/hive/flat_products_for_mapreduce",
            partition_column="category_id",
        )

        print("  -> Partition vat ly: category_id")

        # ----------------------------------------------------
        # 5. TSV KHONG PARTITION CHO MAPREDUCE CO BAN
        # ----------------------------------------------------
        print("\n[5/5] Ghi TSV cho Hadoop MapReduce...")

        (
            df_flat_products
            .select(
                "id",
                "name",
                "source_id",
                "brand_id",
                "source_name",
                "category_name",
                "brand_name",
                "num_images",        # BO SUNG
                "price",
                "market_price",      # BO SUNG
                "discount_amount",   # BO SUNG
                "discount_percent",
                "has_discount",      # BO SUNG
                "sold_count",
                "stock_quantity",    # BO SUNG
                "scraped_at",        # BO SUNG
                "category_id",
            )
            .write
            .mode("overwrite")
            .option("sep", "\t")
            .option("header", "false")
            .csv(f"{HDFS_BASE}/mapreduce_input")
        )

        print("\n====================================================")
        print("HOAN TAT ETL: MYSQL WINDOWS -> HDFS")
        print("====================================================")

    finally:
        spark.stop()


if __name__ == "__main__":
    run_etl()