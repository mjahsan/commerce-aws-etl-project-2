import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Not necessary if the script is directly written in AWS Glue Scriptbook
# spark = SparkSession.builder
#        .appName("commerce_transformation")
#        .getOrCreate()

# Loading json files
user_df = (spark.read.json("s3://commerce-processing/silver_commerce/user/"))
orders_df = (spark.read.json("s3://commerce-processing/silver_commerce/orders/"))
events_df = (spark.read.json("s3://commerce-processing/silver_commerce/events/"))

# # Basic sanity checks
# print("Users count:", user_df.count())
# print("Orders count:", orders_df.count())
# print("Events count:", events_df.count())
#
# user_df.printSchema()
# orders_df.printSchema()
# events_df.printSchema()

# Creating TempView for SQL
user_df.createOrReplaceTempView("user")
events_df.createOrReplaceTempView("events")
orders_df.createOrReplaceTempView("orders")

user_cleaned = spark.sql("""
            SELECT
                user_id,
                country,
                device_type,
                marketing_source,
                CAST(signup_date AS DATE) as signup_date
            FROM user
            """
)
user_cleaned.createOrReplaceTempView("user_cleaned")

orders_cleaned = spark.sql("""
                SELECT
                    user_id,
                    order_id,
                    currency,
                    order_amount,
                    CAST(order_timestamp AS TIMESTAMP) as order_timestamp,
                    payment_status,
                    product_id
                FROM orders
                """
)
orders_cleaned.createOrReplaceTempView("orders_cleaned")

events_cleaned = spark.sql("""
                    SELECT
                        user_id,
                        device_type,
                        event_id,
                        CAST(event_timestamp AS TIMESTAMP) as event_timestamp,
                        event_type,
                        product_id,
                        session_id
                    FROM events
                    """
)
events_cleaned.createOrReplaceTempView("events_cleaned")

user_activity = spark.sql("""
                    SELECT
                        u.user_id,
                        u.country,
                        COUNT(DISTINCT e.event_id) AS total_events,
                        COUNT(DISTINCT o.order_id) AS total_orders,
                        COALESCE(SUM(o.order_amount),0) AS revenue
                    FROM user_cleaned u
                    LEFT JOIN events_cleaned e
                        ON u.user_id = e.user_id
                    LEFT JOIN orders_cleaned o
                        ON u.user_id = o.user_id
                    GROUP BY u.user_id,u.country                      
                    """
)

(
user_activity.coalesce(4)
.write.mode("overwrite")
.parquet("s3://commerce-processing/gold_commerce/")
) # make sure that gold_commerce folder does not exist prior to Glue run. It might throw an error in some cases. If the folder is existing, delete it before running the script. Glue automatically creates gold_commerce folder
job.commit()