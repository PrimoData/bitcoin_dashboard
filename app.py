import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os

allium_key = os.environ.get('ALLIUM_KEY')

page_icon = "https://assets.coingecko.com/coins/images/1/thumb/bitcoin.png"
st.set_page_config(page_title="Bitcoin Dashboard", page_icon=page_icon, layout="wide")

st.title('Bitcoin Dashboard')

st.markdown('''
<style>
/*center metric label*/
[data-testid="stMetricLabel"] {
    justify-content: center;
}

/*center metric value*/
[data-testid="stMetricValue"] {
    color: #F7931A;
}

[data-testid="metric-container"] {
    box-shadow: 2px 2px 2px #FFFFFF;
    border: 2px solid #f7931a;
    padding: 10px;
}

.css-z5fcl4 {
    padding-top: 36px;
    padding-bottom: 36px;
}

.css-1544g2n {
    padding-top: 36px;
}
</style>

<strong>Data Powered by: </strong>[Allium](https://www.allium.so/), [Bitcoin Visuals](https://bitcoinvisuals.com/resources), [Blockchain.com](https://www.blockchain.com/explorer/api).<br />
<strong>Created by: </strong>[Primo Data](https://primodata.org/).
  
''', unsafe_allow_html=True)

# Define date range dropdown options
date_ranges = {
    "All": 365*20,
    "Last 7 Days": 7,
    "Last 30 Days": 30,
    "Last 90 Days": 90,
    "Last Year": 365,
    "Last 5 Years": 365*5
}

# Create a sidebar panel for date filters
with st.sidebar:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image('https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Bitcoin.svg/1200px-Bitcoin.svg.png', width=70)
    with col2:
        st.image('https://upload.wikimedia.org/wikipedia/commons/5/5a/Lightning_Network.svg', width=70)
    with col3:
        st.image('assets/img/ordinals_logo.png', width=70)
    st.header("Filters")
    date_range = st.sidebar.selectbox("Date Range", options=list(date_ranges.keys()))
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=date_ranges[date_range])   

# Define the URLs for the data sources
bc_url = 'https://api.blockchain.info/stats'
addr_url = 'https://api.blockchain.info/charts/n-unique-addresses?timespan=all&format=json'
btc_lt_url = 'https://bitcoinvisuals.com/static/data/data_daily.csv'
btc_lt_file = 'assets/data/data_daily.csv'

# Fetch data from Allium API
def allium_api(query_id):
    response = requests.post(
        f"https://api.allium.so/api/v1/explorer/queries/{query_id}/run",
        json={},
        headers={"X-API-Key": allium_key},
    )
    data = response.json()
    df = pd.DataFrame(data['data']).rename(columns={"dt":"Date"})
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by="Date", ascending=False)
    return df

@st.cache_data
def load_data():
    # Get NFT created data from Allium
    nfts_new_df = allium_api("7qtKVMAIEO8izZAdF4MS")

    # Get NFT sold data from Allium
    nfts_sold_df = allium_api("wCl0X5q3YsaHTd0btmGs")    

    btc_price_24h = allium_api("aGLdPtQuQETbZkq8rV0v")['usd_price'].iloc[0]

    # Get historical Lightning & BTC data from BitcoinVisuals.com
    #btc_lt_df = pd.read_csv(btc_lt_url, storage_options={'User-Agent': 'Mozilla/5.0'}, usecols=["day","nodes_total","capacity_total","price_btc","tx_count_total_sum","marketcap_btc"]).rename(columns={'day':'Date'}).query('Date != "2022-04-25"')
    btc_lt_df = pd.read_csv(btc_lt_file, usecols=["day","nodes_total","capacity_total","price_btc","tx_count_total_sum","marketcap_btc"]).rename(columns={'day':'Date'}).query('Date != "2022-04-25"')
    btc_lt_df['Date'] = pd.to_datetime(btc_lt_df['Date'])
    btc_lt_df = btc_lt_df.sort_values(by="Date", ascending=False)

    # Get historical BTC address data from Blockchain.com
    addr_data = requests.get(addr_url).json()
    addr_df = pd.DataFrame(addr_data['values']).rename(columns={"x":"Date","y":"Addresses"})
    addr_df['Date'] = pd.to_datetime(addr_df['Date'], unit='s')
    addr_df = addr_df.sort_values(by="Date", ascending=False)

    return nfts_new_df, nfts_sold_df, btc_lt_df, addr_df, btc_price_24h

nfts_new_df, nfts_sold_df, btc_lt_df, addr_df, btc_price_24h = load_data()

# Get summary BTC data from Blockchain.com
bc_data = requests.get(bc_url).json()

# Extract the data we need from the JSON response
btc_price = bc_data['market_price_usd']
btc_price_chg = ((btc_price - btc_price_24h) / btc_price_24h ) * 100

btc_total = bc_data['totalbc']/100000000
btc_total_chg = ((btc_total - ( btc_total - (144*6.25))) / ( btc_total - (144*6.25)) ) * 100

ln_capacity = btc_lt_df.iloc[1,:]['capacity_total']
ln_capacity_chg = ((ln_capacity - btc_lt_df.iloc[2,:]['capacity_total']) / btc_lt_df.iloc[2,:]['capacity_total'] ) * 100

ln_nodes = btc_lt_df.iloc[1,:]['nodes_total']
ln_nodes_chg = ((ln_nodes - btc_lt_df.iloc[2,:]['nodes_total']) / btc_lt_df.iloc[2,:]['nodes_total'] ) * 100

btc_tx_today = btc_lt_df.iloc[1,:]['tx_count_total_sum']
btc_tx_chg = ((btc_tx_today - btc_lt_df.iloc[2,:]['tx_count_total_sum']) / btc_lt_df.iloc[2,:]['tx_count_total_sum'] ) * 100

addr_today = addr_df.iloc[0,:]['Addresses']
addr_chg = ((addr_today - addr_df.iloc[1,:]['Addresses']) / addr_df.iloc[1,:]['Addresses'] ) * 100

nfts_new_summed_df = nfts_new_df.groupby("Date")['nft_count'].sum().to_frame().sort_index(ascending=False)
nfts_new_today = nfts_new_summed_df.iloc[1,:]['nft_count']
nfts_new_chg = ((nfts_new_today - nfts_new_summed_df.iloc[2,:]['nft_count']) / nfts_new_summed_df.iloc[2,:]['nft_count'] ) * 100

nfts_sold_summed_df = nfts_sold_df.groupby("Date")['total_sales_usd'].sum().to_frame().sort_index(ascending=False)
nfts_sold_today = nfts_sold_summed_df.iloc[1,:]['total_sales_usd']
nfts_sold_chg = ((nfts_sold_today - nfts_sold_summed_df.iloc[2,:]['total_sales_usd']) / nfts_sold_summed_df.iloc[2,:]['total_sales_usd'] ) * 100 

# Filter the data based on the user's input
addr_df = addr_df.loc[(addr_df['Date'] >= pd.Timestamp(start_date)) & (addr_df['Date'] <= pd.Timestamp(end_date))]
btc_lt_df = btc_lt_df.loc[(btc_lt_df['Date'] >= pd.Timestamp(start_date)) & (btc_lt_df['Date'] <= pd.Timestamp(end_date))]
nfts_sold_df = nfts_sold_df.loc[(nfts_sold_df['Date'] >= pd.Timestamp(start_date)) & (nfts_sold_df['Date'] <= pd.Timestamp(end_date))]
nfts_new_df = nfts_new_df.loc[(nfts_new_df['Date'] >= pd.Timestamp(start_date)) & (nfts_new_df['Date'] <= pd.Timestamp(end_date))]

# Display the metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label='Current Bitcoin Price (USD)', value=f"${btc_price:,.0f}", delta=f"{btc_price_chg:,.2f}%")
    st.metric(label='Bitcoin Transactions (24h)', value=f"{btc_tx_today:,.0f}", delta=f"{btc_tx_chg:,.2f}%")
with col2:
    st.metric(label='Total Bitcoin', value=f"{btc_total:,.0f}", delta=f"{btc_total_chg:,.3f}%")
    st.metric(label='Bitcoin Addresses (24h)', value=f"{addr_today:,.0f}", delta=f"{addr_chg:,.2f}%")
with col3:
    st.metric(label='Total Lightning Capacity (BTC)', value=f"{ln_capacity:,.0f}", delta=f"{ln_capacity_chg:,.2f}%")
    st.metric(label='Bitcoin NFTs Created (24h)', value=f"{nfts_new_today:,.0f}", delta=f"{nfts_new_chg:,.2f}%")
with col4:
    st.metric(label='Total Lightning Nodes', value=f"{ln_nodes:,.0f}", delta=f"{ln_nodes_chg:,.2f}%")
    st.metric(label='Bitcoin NFTs Sold (24h)', value=f"${nfts_sold_today:,.0f}", delta=f"{nfts_sold_chg:,.2f}%")

# Create a line chart of daily prices
chart_price = px.line(btc_lt_df, x='Date', y='price_btc', title='Daily Bitcoin Price ($USD)', color_discrete_sequence=['#F7931A'])
chart_price.update_layout(
    yaxis_title='Price ($USD)',
    font=dict(size=12),
    title=dict(font=dict(size=16))
)
st.plotly_chart(chart_price, use_container_width=True)

st.markdown('<hr />', unsafe_allow_html=True)

##### Bitcoin Blockchain - Title
col1, col2 = st.columns([1, 11])
with col1:
    st.image('https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Bitcoin.svg/1200px-Bitcoin.svg.png', width=70)
with col2:
    st.header('Bitcoin Blockchain')
# Bitcoin Blockchain - Charts
col1, col2 = st.columns(2)
# Create a line chart of daily addresses
with col1:
    chart_txn = px.line(btc_lt_df, x='Date', y='tx_count_total_sum', title='Daily Transactions', color_discrete_sequence=['#F7931A'])
    chart_txn.update_layout(
        yaxis_title='Transactions',
        font=dict(size=12),
        title=dict(font=dict(size=16))
    )
    st.plotly_chart(chart_txn, use_container_width=True)
# Create a line chart of daily transactions
with col2:
    chart_addr = px.line(addr_df, x='Date', y='Addresses', title='Daily Active Addresses', color_discrete_sequence=['#F7931A'])
    chart_addr.update_layout(
        yaxis_title='Active Addresses',
        font=dict(size=12),
        title=dict(font=dict(size=16))
    )    
    st.plotly_chart(chart_addr, use_container_width=True)

st.markdown('<hr />', unsafe_allow_html=True)

##### Bitcoin Lightning Network - Title
col1, col2 = st.columns([1, 11])
with col1:
    st.image('https://upload.wikimedia.org/wikipedia/commons/5/5a/Lightning_Network.svg', width=70)
with col2:
    st.header('Bitcoin Lightning Network')
# Bitcoin Lightning Network - Charts
col1, col2 = st.columns(2)
with col1:
    # Create a line chart of daily capacity
    chart_lightning_capacity = px.line(btc_lt_df, x='Date', y='capacity_total', title='Daily Lightning Capacity', color_discrete_sequence=['#F7931A'])
    chart_lightning_capacity.update_layout(
        yaxis_title='Capacity (BTC)',
        font=dict(size=12),
        title=dict(font=dict(size=16))
    )
    st.plotly_chart(chart_lightning_capacity, use_container_width=True)    
with col2:
    # Create a line chart of daily nodes
    chart_lightning_nodes = px.line(btc_lt_df, x='Date', y='nodes_total', title='Daily Lightning Node Count', color_discrete_sequence=['#F7931A'])
    chart_lightning_nodes.update_layout(
        yaxis_title='Nodes',
        font=dict(size=12),
        title=dict(font=dict(size=16))
    )
    st.plotly_chart(chart_lightning_nodes, use_container_width=True)


st.markdown('<hr />', unsafe_allow_html=True)

##### Bitcoin NFTs - Title
col1, col2 = st.columns([1, 11])
with col1:
    st.image('assets/img/ordinals_logo.png', width=70)
with col2:
    st.header('Bitcoin NFTs (aka Ordinals)')
# Bitcoin NFTs/Ordinals - Charts
col1, col2 = st.columns(2)
with col1:
    # Create a line chart of daily nodes
    chart_nfts_created = px.bar(nfts_new_df, x='Date', y='nft_count', color='nft_type', barmode='stack', title='Daily NFTs Created')
    chart_nfts_created.update_layout(
        yaxis_title='NFT Count',
        font=dict(size=12),
        title=dict(font=dict(size=16))
    )
    st.plotly_chart(chart_nfts_created, use_container_width=True)
with col2:
    # Create a line chart of daily nodes
    chart_nfts_sold = px.bar(nfts_sold_df, x='Date', y='total_sales_usd', color='marketplace', barmode='stack', title='Daily NFTs Sales ($USD)')
    chart_nfts_sold.update_layout(
        yaxis_title='Sales ($USD)',
        font=dict(size=12),
        title=dict(font=dict(size=16))
    )
    st.plotly_chart(chart_nfts_sold, use_container_width=True)

components.html('''
<style>
mash-donate-button::part(button-solid){
    margin-left: 260px;
    margin-top: 260px;
}
</style>
  <script>
    window.MashSettings = {
      id: "dd9f18f3-6539-4967-97bc-de1b6bac7b7c"
    };
    var loader = function () {
      window.Mash.init();
    };
    var script = document.createElement("script");
    script.type = "text/javascript";
    script.defer = true;
    script.onload = loader;
    script.src = "https://app.mash.com/sdk/sdk.js";
    var head = document.getElementsByTagName("head")[0];
    head.appendChild(script);
  </script>
  <mash-donate-button handle="my-handle" mode="all" button-size="md" button-variant="solid">
  </mash-donate-button>
''', height=400, width=400)

st.markdown(
    """
    <style>
        iframe[width="400"] {
            position: fixed;
            bottom: 0px;
            right: 20px;
        } 
    </style>
    """,
    unsafe_allow_html=True,
)
