from snowflake.snowpark import Session
import json
from decimal import Decimal

# Connect to Snowflake using the saved connection profile
session = Session.builder.config("connection_name", "chewy-chewy").create()

# ---------------------
# Feature Query Functions
# ---------------------

def get_total_food_lbs(session, customer_id):
    query = """
WITH parsed_food AS (
  SELECT
    ol.product_id,
    p.name AS product_name,
    ol.order_line_quantity,

    -- Extract numeric weight value
    TRY_TO_NUMBER(
      REGEXP_SUBSTR(p.name, '(\\d+(\\.\\d+)?)(\\s|-)?(oz|lb|mg)', 1, 1, 'e', 1)
    ) AS extracted_weight,

    -- Extract unit
    REGEXP_SUBSTR(p.name, '(\\d+(\\.\\d+)?)(\\s|-)?(oz|lb|mg)', 1, 1, 'e', 4) AS unit,

    -- Extract pack size
    TRY_TO_NUMBER(
      REGEXP_SUBSTR(p.name, '(\\d+)\\s?(pack|count|ct|bags?)', 1, 1, 'e', 1)
    ) AS pack_count,

    -- Normalized weight in lbs
    CASE 
      WHEN REGEXP_SUBSTR(p.name, '(\\d+(\\.\\d+)?)(\\s|-)?(oz|lb|mg)', 1, 1, 'e', 4) = 'oz'
        THEN TRY_TO_NUMBER(REGEXP_SUBSTR(p.name, '(\\d+(\\.\\d+)?)(\\s|-)?(oz|lb|mg)', 1, 1, 'e', 1)) / 16
      WHEN REGEXP_SUBSTR(p.name, '(\\d+(\\.\\d+)?)(\\s|-)?(oz|lb|mg)', 1, 1, 'e', 4) = 'mg'
        THEN TRY_TO_NUMBER(REGEXP_SUBSTR(p.name, '(\\d+(\\.\\d+)?)(\\s|-)?(oz|lb|mg)', 1, 1, 'e', 1)) / 453592
      WHEN REGEXP_SUBSTR(p.name, '(\\d+(\\.\\d+)?)(\\s|-)?(oz|lb|mg)', 1, 1, 'e', 4) = 'lb'
        THEN TRY_TO_NUMBER(REGEXP_SUBSTR(p.name, '(\\d+(\\.\\d+)?)(\\s|-)?(oz|lb|mg)', 1, 1, 'e', 1))
      ELSE NULL
    END AS weight_in_lbs,

    -- Final food weight = weight × qty × pack size
    CASE 
      WHEN REGEXP_SUBSTR(p.name, '(\\d+(\\.\\d+)?)(\\s|-)?(oz|lb|mg)', 1, 1, 'e', 4) = 'oz'
        THEN (TRY_TO_NUMBER(REGEXP_SUBSTR(p.name, '(\\d+(\\.\\d+)?)(\\s|-)?(oz|lb|mg)', 1, 1, 'e', 1)) / 16)
          * ol.order_line_quantity * COALESCE(TRY_TO_NUMBER(REGEXP_SUBSTR(p.name, '(\\d+)\\s?(pack|count|ct|bags?)', 1, 1, 'e', 1)), 1)
      WHEN REGEXP_SUBSTR(p.name, '(\\d+(\\.\\d+)?)(\\s|-)?(oz|lb|mg)', 1, 1, 'e', 4) = 'mg'
        THEN (TRY_TO_NUMBER(REGEXP_SUBSTR(p.name, '(\\d+(\\.\\d+)?)(\\s|-)?(oz|lb|mg)', 1, 1, 'e', 1)) / 453592)
          * ol.order_line_quantity * COALESCE(TRY_TO_NUMBER(REGEXP_SUBSTR(p.name, '(\\d+)\\s?(pack|count|ct|bags?)', 1, 1, 'e', 1)), 1)
      WHEN REGEXP_SUBSTR(p.name, '(\\d+(\\.\\d+)?)(\\s|-)?(oz|lb|mg)', 1, 1, 'e', 4) = 'lb'
        THEN TRY_TO_NUMBER(REGEXP_SUBSTR(p.name, '(\\d+(\\.\\d+)?)(\\s|-)?(oz|lb|mg)', 1, 1, 'e', 1))
          * ol.order_line_quantity * COALESCE(TRY_TO_NUMBER(REGEXP_SUBSTR(p.name, '(\\d+)\\s?(pack|count|ct|bags?)', 1, 1, 'e', 1)), 1)
      ELSE 0
    END AS total_food_lbs
  FROM edldb.ecom.order_line AS ol
  JOIN edldb.pdm.product AS p
    ON ol.product_id = p.product_id
  WHERE ol.customer_id = 958100772
    AND ol.order_status = 'D'
    AND p.is_food_flag = TRUE
)

-- Final output: just total
SELECT ROUND(SUM(total_food_lbs), 2) AS total_lbs_consumed
FROM parsed_food;
    """


    result = session.sql(query).collect()
    return [row.as_dict() for row in result]

def get_donations(session, customer_id):
    query = f"""
    SELECT
      olb.CUSTOMER_ID,
      olb.ORDER_ID,
      olb.ORDER_PLACED_DTTM,
      olb.DONATION_ORG_ID,
      olb.PRODUCT_ID,
      p.PRODUCT_NAME,
      olb.PART_NUMBER,
      olb.ORDER_LINE_QUANTITY AS DONATED_QTY,
      olb.ORDER_LINE_TOTAL_PRICE AS DONATION_VALUE
    FROM EDLDB.ECOM.ORDER_LINE_BASE olb
    LEFT JOIN EDLDB.CHEWYBI.PRODUCTS p ON olb.PRODUCT_ID = p.PRODUCT_ID
    WHERE olb.DONATION_ORG_ID IS NOT NULL
      AND olb.ORDER_LINE_QUANTITY > 0
      AND olb.CUSTOMER_ID = {customer_id}
    ORDER BY olb.ORDER_PLACED_DTTM
    """
    result = session.sql(query).collect()
    return [row.as_dict() for row in result]

def get_milestone(session, customer_id):
    query = f"""
    SELECT 
  DATEDIFF(MONTH, registration_date, CURRENT_DATE()) AS months_with_chewy
FROM EDLDB.CDM.CUSTOMER_AGGREGATE
WHERE CUSTOMER_ID = {customer_id}

    """
    result = session.sql(query).collect()
    return [row.as_dict() for row in result]

def get_most_reordered(session, customer_id):
    query = f"""
    SELECT
    ol.product_id,
    p.NAME,
    MAX(p.FULLIMAGE) AS full_image,  -- Safe way to grab the image
    SUM(ol.order_line_quantity) AS total_quantity_ordered
FROM edldb.ecom.order_line_base AS ol
JOIN edldb.pdm.product AS p
    ON ol.product_id = p.product_id
WHERE ol.order_status = 'D'
  AND ol.customer_id = {customer_id}
GROUP BY ol.product_id, p.NAME
ORDER BY total_quantity_ordered DESC
LIMIT 1;

    """
    result = session.sql(query).collect()
    return [row.as_dict() for row in result]

def get_cuddliest_month(session, customer_id):
    query = f"""
   SELECT
  TO_CHAR(ol.order_placed_dttm, 'Mon') AS month,
  COUNT(*) AS total_orders
FROM edldb.ecom.order_line_base AS ol
WHERE ol.order_status = 'D'
  AND ol.customer_id = {customer_id}
  AND YEAR(ol.order_placed_dttm) = 2025
GROUP BY TO_CHAR(ol.order_placed_dttm, 'Mon')
ORDER BY total_orders DESC
LIMIT 1;

    """
    result = session.sql(query).collect()
    return [row.as_dict() for row in result]

def get_autoship_savings(session, customer_id):
    query = f"""
    SELECT CUSTOMER_ID, LIFETIME_SAVINGS 
FROM EDLDB.ITEM_LEVEL_AUTOSHIP.CUSTOMER_INFO 
WHERE CUSTOMER_ID = {customer_id}

    """
    result = session.sql(query).collect()
    return [row.as_dict() for row in result]

# ---------------------
# Orchestrator
# ---------------------

def get_all_customer_features(session, customer_id):
    features = {}

    for feature_name, query_fn in {
        "total_food_lbs": get_total_food_lbs,
        "donations": get_donations,
        "milestone_years": get_milestone,
        "most_reordered": get_most_reordered,
        "cuddliest_month": get_cuddliest_month,
        "autoship_savings": get_autoship_savings,
    }.items():
        try:
            result = query_fn(session, customer_id)
            features[feature_name] = result if result else []
        except Exception as e:
            print(f"⚠️ Error loading {feature_name}: {e}")
            features[feature_name] = []

    return features

# ---------------------
# Run It
# ---------------------

if __name__ == "__main__":
    customer_id = input("Enter customer ID: ").strip()
    result = get_all_customer_features(session, customer_id)

    # Print results
    for key, value in result.items():
      print(f"\n🔹 {key.upper()} 🔹")
      if not value:
        print("No data available.")
      else:
        print(value)

          



    # Optional: save to JSON (with Decimal handling)
    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, 'isoformat'):  # Handle datetime objects
            return obj.isoformat()
        raise TypeError(f'Object of type {type(obj)} is not JSON serializable')
    
    with open(f"customer_{customer_id}_features.json", "w") as f:
        json.dump(result, f, indent=2, default=decimal_default)




