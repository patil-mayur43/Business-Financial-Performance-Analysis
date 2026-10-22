import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Business Financial Performance Analysis", page_icon="📊", layout="wide")
st.title("📊 Business Financial Performance Analysis")
st.write("Upload a company's financial CSV or test the dashboard with the sample dataset.")

REQUIRED = ["Fiscal_Year","Revenue","Cost_of_Revenue","R_and_D","Sales_and_Marketing",
            "General_and_Administrative","Operating_Income","Net_Income"]

SAMPLE_FILE = "sample_company_dataset.csv"

with st.sidebar:
    st.header("Dataset")
    uploaded = st.file_uploader("Drag and drop another company's CSV here", type=["csv"])
    st.caption("Required CSV columns:")
    st.code(", ".join(REQUIRED))
    st.caption("Use one consistent currency and unit for all monetary values.")

@st.cache_data
def load_sample():
    return pd.read_csv(SAMPLE_FILE)

try:
    if uploaded is not None:
        raw = pd.read_csv(uploaded)
        source = f"Uploaded: {uploaded.name}"
    else:
        raw = load_sample()
        source = "Included synthetic sample dataset (not real company data)"
except Exception as e:
    st.error(f"Could not read CSV: {e}")
    st.stop()

missing = [c for c in REQUIRED if c not in raw.columns]
if missing:
    st.error("Missing required columns: " + ", ".join(missing))
    st.info("Download the sample CSV template below and format your company's verified data using those column names.")
    st.stop()

df = raw[REQUIRED].copy()
for c in REQUIRED:
    df[c] = pd.to_numeric(df[c], errors="coerce")
if df.isna().any().any():
    st.error("Some required values are blank or non-numeric. Correct the CSV and upload it again.")
    st.stop()
df = df.drop_duplicates("Fiscal_Year").sort_values("Fiscal_Year")
if df.empty or (df["Revenue"] <= 0).any():
    st.error("Dataset is empty or contains revenue values less than or equal to zero.")
    st.stop()

df["Gross_Profit"] = df["Revenue"] - df["Cost_of_Revenue"]
df["Operating_Expenses"] = df["R_and_D"] + df["Sales_and_Marketing"] + df["General_and_Administrative"]
df["Operating_Margin"] = df["Operating_Income"] / df["Revenue"] * 100
df["Net_Profit_Margin"] = df["Net_Income"] / df["Revenue"] * 100
df["Revenue_Growth"] = df["Revenue"].pct_change() * 100
df["Operating_Income_Growth"] = df["Operating_Income"].pct_change() * 100
df["Net_Income_Growth"] = df["Net_Income"].pct_change() * 100

st.caption(f"Dataset: {source} | {len(df)} fiscal-year rows")
with st.sidebar:
    years = sorted(df["Fiscal_Year"].astype(int).tolist())
    selected = st.multiselect("Filter fiscal years", years, default=years)
if not selected:
    st.warning("Select at least one year in the sidebar.")
    st.stop()
view = df[df["Fiscal_Year"].isin(selected)].sort_values("Fiscal_Year")
latest = view.iloc[-1]

st.subheader(f"Financial Overview — FY{int(latest['Fiscal_Year'])}")
a,b,c,d = st.columns(4)
a.metric("Revenue", f"{latest['Revenue']:,.0f}")
b.metric("Operating Income", f"{latest['Operating_Income']:,.0f}")
c.metric("Net Income", f"{latest['Net_Income']:,.0f}")
d.metric("Net Profit Margin", f"{latest['Net_Profit_Margin']:.2f}%")
st.caption("Monetary values use the currency and scale of the uploaded CSV; the app does not guess either.")

st.subheader("1. Revenue Trend")
st.plotly_chart(px.line(view, x="Fiscal_Year", y="Revenue", markers=True, title="Revenue by Fiscal Year"), use_container_width=True)

st.subheader("2. Revenue vs Profit")
long = view.melt(id_vars=["Fiscal_Year"], value_vars=["Revenue","Operating_Income","Net_Income"], var_name="Metric", value_name="Amount")
st.plotly_chart(px.bar(long, x="Fiscal_Year", y="Amount", color="Metric", barmode="group", title="Revenue, Operating Income and Net Income"), use_container_width=True)

st.subheader("3. Operating Expense Categories")
expenses = view.melt(id_vars=["Fiscal_Year"], value_vars=["R_and_D","Sales_and_Marketing","General_and_Administrative"], var_name="Expense Category", value_name="Amount")
st.plotly_chart(px.bar(expenses, x="Fiscal_Year", y="Amount", color="Expense Category", title="Selected Operating Expenses"), use_container_width=True)

st.subheader("4. Profit Margins")
margins = view.melt(id_vars=["Fiscal_Year"], value_vars=["Operating_Margin","Net_Profit_Margin"], var_name="Margin Type", value_name="Margin (%)")
st.plotly_chart(px.line(margins, x="Fiscal_Year", y="Margin (%)", color="Margin Type", markers=True, title="Operating Margin vs Net Profit Margin"), use_container_width=True)

st.subheader("5. Year-over-Year Growth")
growth = view[["Fiscal_Year","Revenue_Growth","Operating_Income_Growth","Net_Income_Growth"]].rename(columns={
"Fiscal_Year":"Fiscal Year","Revenue_Growth":"Revenue Growth (%)",
"Operating_Income_Growth":"Operating Income Growth (%)","Net_Income_Growth":"Net Income Growth (%)"})
st.dataframe(growth.round(2), use_container_width=True, hide_index=True)

st.subheader("6. Key Insights")
first,last = view.iloc[0],view.iloc[-1]
if len(view) > 1:
    for label,col in [("Revenue","Revenue"),("Operating income","Operating_Income"),("Net income","Net_Income")]:
        pct=(last[col]-first[col])/first[col]*100
        st.write(f"- {label} changed by {pct:.2f}% from FY{int(first['Fiscal_Year'])} to FY{int(last['Fiscal_Year'])}.")
else:
    st.info("Select at least two fiscal years to compare trends.")

st.subheader("7. Financial Data")
st.dataframe(view.round(2), use_container_width=True, hide_index=True)
st.download_button("Download analyzed data", view.to_csv(index=False).encode("utf-8"), "financial_analysis.csv", "text/csv")
st.download_button("Download sample CSV template", load_sample().to_csv(index=False).encode("utf-8"), "sample_company_dataset.csv", "text/csv")
st.caption("Sample values are synthetic for testing. For real-company analysis, use verified financial statements from the company's official investor-relations website.")
