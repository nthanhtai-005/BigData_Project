#!/bin/bash

# 1. KHAI BAO MOI TRUONG
export HADOOP_HOME=/home/hadoopnhom6/hadoop 
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

# 2. DINH NGHIA DUONG DAN 2 THU MUC NGUON TREM HDFS
HDFS_SRC_1="/data/bigdata_ecommerce/hive"
HDFS_SRC_2="/data/bigdata_ecommerce/mapreduce_input"

# Thu muc luu tru cuc bo
LOCAL_BAK_DIR="/home/hadoopnhom6/hdfs_backup"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="$LOCAL_BAK_DIR/hdfs_backup_$TIMESTAMP"

echo "=== BAT DAU SAO LUU 2 THU MUC HDFS ==="

# Tao thu muc backup cuc bo truoc de chua 2 thu muc con
mkdir -p $BACKUP_PATH

# Tien hanh keo tung thu muc ve
echo "Dang keo thu muc hive..."
OUTPUT1=$(hdfs dfs -get $HDFS_SRC_1 $BACKUP_PATH 2>&1)
EXIT_CODE1=$?

echo "Dang keo thu muc mapreduce_input..."
OUTPUT2=$(hdfs dfs -get $HDFS_SRC_2 $BACKUP_PATH 2>&1)
EXIT_CODE2=$?

# 3. PHAN TICH KET QUA
if [ $EXIT_CODE1 -eq 0 ] && [ $EXIT_CODE2 -eq 0 ]; then
    echo "[SUCCESS] THANH CONG RUC RO!"
    echo "Da sao luu 2 thu muc vao an toan tai: $BACKUP_PATH"
else
    echo "[FAILED] HE THONG DA XAY RA LOI"
    echo "Loi thu muc hive (Code $EXIT_CODE1): $OUTPUT1"
    echo "Loi thu muc mapreduce_input (Code $EXIT_CODE2): $OUTPUT2"
fi