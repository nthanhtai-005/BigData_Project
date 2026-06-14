from pyspark.sql import SparkSession


# ============================================================
# CAU HINH KET NOI MYSQL TREN WINDOWS
# ============================================================
MYSQL_HOST = "172.172.0.148"
MYSQL_PORT = "3306"
MYSQL_DATABASE = "bigdata_ecommerce"
MYSQL_USER = "root"
MYSQL_PASSWORD = "nmt1610104"


def run_etl():
    print("====================================================")
    print("KHOI DONG PYSPARK ETL ENGINE")
    print("====================================================")

    # --------------------------------------------------------
    # 1. Khoi tao Spark Session va bat ho tro Hive
    # --------------------------------------------------------
    spark = (
        SparkSession.builder
        .appName("E-commerce ETL Pipeline")
        .enableHiveSupport()
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    try:
        # ----------------------------------------------------
        # 2. Tao database Hive neu chua ton tai
        # ----------------------------------------------------
        print("\n[1/6] Tao database Hive neu chua ton tai...")

        spark.sql("""
            CREATE DATABASE IF NOT EXISTS bigdata_ecommerce
        """)

        # ----------------------------------------------------
        # 3. Cau hinh JDBC ket noi MySQL tren Windows
        # ----------------------------------------------------
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
        # 4. Nap cac bang danh muc tu MySQL sang Hive
        # ----------------------------------------------------
        print("\n[2/6] Nap cac bang danh muc tu MySQL sang Hive...")

        danh_muc = [
            "sources",
            "categories",
            "brands",
        ]

        for table_name in danh_muc:
            print(f"  -> Dang xu ly bang: {table_name}")

            df = spark.read.jdbc(
                url=mysql_url,
                table=table_name,
                properties=mysql_properties,
            )

            (
                df.write
                .mode("overwrite")
                .format("parquet")
                .saveAsTable(f"bigdata_ecommerce.{table_name}")
            )

            print(f"     Da nap {df.count()} dong.")

        # ----------------------------------------------------
        # 5. Nap bang products va partition theo category_id
        # ----------------------------------------------------
        print("\n[3/6] Nap bang products tu MySQL sang Hive...")

        df_products = spark.read.jdbc(
            url=mysql_url,
            table="products",
            properties=mysql_properties,
        )

        print(f"  -> So dong products doc tu MySQL: {df_products.count()}")

        (
            df_products.write
            .mode("overwrite")
            .partitionBy("category_id")
            .format("parquet")
            .saveAsTable("bigdata_ecommerce.final_products")
        )

        print("  -> Da tao bang Hive: bigdata_ecommerce.final_products")
        print("  -> Partition vat ly: category_id")

        # ----------------------------------------------------
        # 6. Tao bang phang phuc vu MapReduce
        # ----------------------------------------------------
        print("\n[4/6] Tao bang phang phuc vu MapReduce...")

        df_flat_products = spark.sql("""
            SELECT
                p.id,
                p.name,
                p.category_id,
                p.source_id,
                p.brand_id,
                s.source_name,
                c.category_name,
                b.brand_name,
                p.price,
                p.discount_percent,
                p.sold_count
            FROM bigdata_ecommerce.final_products AS p
            INNER JOIN bigdata_ecommerce.sources AS s
                ON p.source_id = s.id
            INNER JOIN bigdata_ecommerce.categories AS c
                ON p.category_id = c.id
            INNER JOIN bigdata_ecommerce.brands AS b
                ON p.brand_id = b.id
        """)

        (
            df_flat_products.write
            .mode("overwrite")
            .partitionBy("category_id")
            .format("parquet")
            .saveAsTable(
                "bigdata_ecommerce.flat_products_for_mapreduce"
            )
        )

        print(
            "  -> Da tao bang Hive: "
            "bigdata_ecommerce.flat_products_for_mapreduce"
        )
        print("  -> Partition vat ly: category_id")

        # ----------------------------------------------------
        # 7. Kiem tra danh sach bang Hive
        # ----------------------------------------------------
        print("\n[5/6] Danh sach bang Hive sau khi ETL:")

        spark.sql("""
            SHOW TABLES IN bigdata_ecommerce
        """).show(truncate=False)

        # ----------------------------------------------------
        # 8. Kiem tra tong so dong cua tung bang
        # ----------------------------------------------------
        print("\n[6/6] Kiem tra so dong:")

        spark.sql("""
            SELECT 'sources' AS table_name, COUNT(*) AS total_rows
            FROM bigdata_ecommerce.sources

            UNION ALL

            SELECT 'categories' AS table_name, COUNT(*) AS total_rows
            FROM bigdata_ecommerce.categories

            UNION ALL

            SELECT 'brands' AS table_name, COUNT(*) AS total_rows
            FROM bigdata_ecommerce.brands

            UNION ALL

            SELECT 'final_products' AS table_name, COUNT(*) AS total_rows
            FROM bigdata_ecommerce.final_products

            UNION ALL

            SELECT
                'flat_products_for_mapreduce' AS table_name,
                COUNT(*) AS total_rows
            FROM bigdata_ecommerce.flat_products_for_mapreduce
        """).show(truncate=False)

        print("\n====================================================")
        print("HOAN TAT ETL: MYSQL WINDOWS -> HIVE PARQUET")
        print("====================================================")

    finally:
        spark.stop()


if __name__ == "__main__":
    run_etl()