import streamlit as st
import snowflake.connector
import pandas as pd

st.title("🔍 Snowflake Connection Test")

try:
    # Test connection
    conn = snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"]
    )

    st.success("✅ Connection successful!")

    # Show connection details
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE()")
    wh, db, schema, role = cursor.fetchone()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("⚙️ Warehouse", wh)
        st.metric("📊 Database", db)
    with col2:
        st.metric("📁 Schema", schema)
        st.metric("👤 Role", role)

    st.markdown("---")

    # Test table access
    st.subheader("📋 Table Verification")

    tables = ['properties', 'rooms', 'findings', 'property_risk_scores',
              'room_risk_scores', 'inspection_summaries']

    for table in tables:
        try:
            df = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", conn)
            count = df['count'].iloc[0]
            st.success(f"✅ {table}: {count} rows")
        except Exception as e:
            st.error(f"❌ {table}: {str(e)}")

    st.markdown("---")

    # Test the problematic query
    st.subheader("🎯 Test Property Query")
    prop_df = pd.read_sql("""
        SELECT property_id, address, property_risk_score, property_grade 
        FROM property_risk_scores
    """, conn)
    prop_df.columns = prop_df.columns.str.lower()
    st.dataframe(prop_df, use_container_width=True)

except Exception as e:
    st.error(f"❌ Connection Failed!")
    st.code(str(e))

    st.markdown("---")
    st.subheader("🔧 Troubleshooting Tips")
    st.markdown("""
    1. Check your account identifier is correct (no https:// or .snowflakecomputing.com)
    2. Verify username and password
    3. Ensure warehouse is running in Snowflake
    4. Check role has permissions to access tables
    """)