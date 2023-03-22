import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os

# Set API keys
allium_key = os.environ.get('ALLIUM_KEY')
amboss_key = os.environ.get('AMBOSS_KEY')

page_icon = "https://assets.coingecko.com/coins/images/1/thumb/bitcoin.png"
st.set_page_config(page_title="Bitcoin Dashboard", page_icon=page_icon, layout="wide")

# Configure CSS styles
st.markdown('''
<style>
    #button-links {
        text-decoration:none; 
        background-color:#f7931a; 
        color:white; 
        padding:20px; 
        display:block;
        box-shadow: 2px 2px 2px #FFFFFF;
        margin-bottom: 10px;
    }
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
</style>''', unsafe_allow_html=True)
            
st.title('Bitcoin Dashboard')

# Create panel for navigation
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('''<a href="#bitcoin-blockchain" id='button-links'>
                    <img src= "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Bitcoin.svg/1200px-Bitcoin.svg.png" height='20px'/>
                    Bitcoin Blockchain</a>''', unsafe_allow_html=True)
with col2:
    st.markdown('''<a href="#bitcoin-lightning-network" id='button-links'>
                    <img src= "https://upload.wikimedia.org/wikipedia/commons/5/5a/Lightning_Network.svg" height='20px'/>
                    Lightning Network</a>''', unsafe_allow_html=True)
with col3:
    st.markdown('''<a href="#bitcoin-nfts-aka-ordinals" id='button-links'>
                    <img src= "https://raw.githubusercontent.com/PrimoData/bitcoin_dashboard/main/assets/img/ordinals_logo.png" height='20px'/>
                    Bitcoin NFTs</a>''', unsafe_allow_html=True)
with col4:
    st.markdown('''<a href="#bitcoin-map" id='button-links'>
                    <img src= "https://btcmap.org/images/logo.svg" height='20px'/>
                    Bitcoin Maps</a>''', unsafe_allow_html=True)

# Shoutout data sources
st.caption('''
Data Powered by:
[Allium](https://www.allium.so/), 
[Amboss Space](https://amboss.tech/docs/apiDocs/intro), 
[Bitcoin Visuals](https://bitcoinvisuals.com/resources), 
[Blockchain.com](https://www.blockchain.com/explorer/api),
[BTC Maps](https://btcmap.org/map) &
[Coinbase](https://docs.cloud.coinbase.com/sign-in-with-coinbase/docs/api-prices).<br />
Created by: [Primo Data](https://primodata.org/).
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
    st.header("Filters")
    date_range = st.sidebar.selectbox("Date Range", options=list(date_ranges.keys()))
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=date_ranges[date_range])   

# Fetch data from Allium API
def get_allium_data(query_id):
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

def get_blockchaincom_data(url, col):
    data = requests.get(url).json()
    df = pd.DataFrame(data['values']).rename(columns={"x":"Date","y":col})
    df['Date'] = pd.to_datetime(df['Date'], unit='s')
    df = df.sort_values(by="Date", ascending=False)
    return df  
    
@st.cache_data
def load_data():
    # Get NFT created data from Allium
    nfts_new_df = get_allium_data("7qtKVMAIEO8izZAdF4MS")

    # Get NFT sold data from Allium
    nfts_sold_df = get_allium_data("wCl0X5q3YsaHTd0btmGs")    

    # Get Lightning Network data from Amboss API
    headers = {
        'Authorization': f'Bearer {amboss_key}',
        'Content-Type': 'application/json'
    }
    body = {
        'query': '''
                query ExampleQuery {
                getNetworkMetrics {
                    all_time_series {
                    series {
                        name
                        series {
                        active_nodes
                        total_capacity
                        date
                        }
                    }
                    }
                }
                }
                '''
    }
    response = requests.post('https://api.amboss.space/graphql', headers=headers, json=body)
    data = response.json()['data']
    df_start = pd.DataFrame(data['getNetworkMetrics']['all_time_series']['series'][1]['series']).query("date < '2022-05-18'")
    df_end = pd.DataFrame(data['getNetworkMetrics']['all_time_series']['series'][0]['series'])
    lightning_df = pd.concat([df_start, df_end]).rename(columns={"date":"Date"})
    lightning_df['Date'] = pd.to_datetime(lightning_df['Date']).dt.tz_localize(None)
    lightning_df = lightning_df.sort_values(by="Date", ascending=False).query('Date != "2022-04-25"')
    lightning_df['total_capacity'] = lightning_df['total_capacity'] / 100000000

    # Get historical BTC address data from Blockchain.com
    price_url = 'https://api.blockchain.info/charts/market-price?timespan=all&format=json'
    price_df = get_blockchaincom_data(price_url, "Prices")

    # Get historical BTC address data from Blockchain.com
    addr_url = 'https://api.blockchain.info/charts/n-unique-addresses?timespan=all&format=json'
    addr_df = get_blockchaincom_data(addr_url, "Addresses")

    # Get historical BTC address data from Blockchain.com
    tx_url = 'https://api.blockchain.info/charts/n-transactions?timespan=all&format=json'
    tx_df = get_blockchaincom_data(tx_url, "Transactions")

    # Get Total BTC from Blockchain.com
    btc_total_url = 'https://api.blockchain.info/stats'
    btc_total = requests.get(btc_total_url).json()['totalbc']/100000000

    return nfts_new_df, nfts_sold_df, lightning_df, price_df, addr_df, tx_df, btc_total

nfts_new_df, nfts_sold_df, lightning_df, price_df, addr_df, tx_df, btc_total = load_data()

# Get Current BTC Price and % 24 hr Change from Coinbase
response = requests.get('https://api.coinbase.com/v2/prices/BTC-USD/spot')
price_now = float(response.json()['data']['amount'])
response = requests.get('https://api.coinbase.com/v2/prices/BTC-USD/spot?date=' + (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d'))
price_24h_ago = float(response.json()['data']['amount'])
price_chg = ((price_now - price_24h_ago) / price_24h_ago) * 100

btc_total_chg = ((btc_total - ( btc_total - (144*6.25))) / ( btc_total - (144*6.25)) ) * 100

ln_capacity = lightning_df.iloc[1,:]['total_capacity']
ln_capacity_chg = ((ln_capacity - lightning_df.iloc[2,:]['total_capacity']) / lightning_df.iloc[2,:]['total_capacity'] ) * 100

ln_nodes = lightning_df.iloc[0,:]['active_nodes']
ln_nodes_chg = ((ln_nodes - lightning_df.iloc[1,:]['active_nodes']) / lightning_df.iloc[1,:]['active_nodes'] ) * 100

tx_today = tx_df.iloc[0,:]['Transactions']
tx_chg = ((tx_today - tx_df.iloc[1,:]['Transactions']) / tx_df.iloc[1,:]['Transactions'] ) * 100

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
lightning_df = lightning_df.loc[(lightning_df['Date'] >= pd.Timestamp(start_date)) & (lightning_df['Date'] <= pd.Timestamp(end_date))]
nfts_sold_df = nfts_sold_df.loc[(nfts_sold_df['Date'] >= pd.Timestamp(start_date)) & (nfts_sold_df['Date'] <= pd.Timestamp(end_date))]
nfts_new_df = nfts_new_df.loc[(nfts_new_df['Date'] >= pd.Timestamp(start_date)) & (nfts_new_df['Date'] <= pd.Timestamp(end_date))]

# Display the metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label='Current Bitcoin Price (USD)', value=f"${price_now:,.0f}", delta=f"{price_chg:,.2f}%")
    st.metric(label='Bitcoin Transactions (24h)', value=f"{tx_today:,.0f}", delta=f"{tx_chg:,.2f}%")
with col2:
    st.metric(label='Total Bitcoin', value=f"{btc_total:,.0f}", delta=f"{btc_total_chg:,.3f}%")
    st.metric(label='Bitcoin Addresses (24h)', value=f"{addr_today:,.0f}", delta=f"{addr_chg:,.2f}%")
with col3:
    st.metric(label='Total Lightning Capacity (BTC)', value=f"{ln_capacity:,.0f}", delta=f"{ln_capacity_chg:,.2f}%")
    st.metric(label='Bitcoin NFTs Created (24h)', value=f"{nfts_new_today:,.0f}", delta=f"{nfts_new_chg:,.2f}%")
with col4:
    st.metric(label='Total Lightning Nodes', value=f"{ln_nodes:,.0f}", delta=f"{ln_nodes_chg:,.2f}%")
    st.metric(label='Bitcoin NFTs Sold (24h)', value=f"${nfts_sold_today:,.0f}", delta=f"{nfts_sold_chg:,.2f}%")

# Bitcoin Pricing
chart_price = px.line(price_df, x='Date', y='Prices', title='Daily Bitcoin Price ($USD)', color_discrete_sequence=['#F7931A'])
chart_price.update_layout(yaxis_title='Price ($USD)')
st.plotly_chart(chart_price, use_container_width=True)

st.markdown('<hr />', unsafe_allow_html=True)

# Bitcoin Blockchain - Title
col1, col2 = st.columns([1, 11])
with col1:
    st.image('https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Bitcoin.svg/1200px-Bitcoin.svg.png', width=70)
with col2:
    st.header('Bitcoin Blockchain')
# Bitcoin Blockchain - Charts
col1, col2 = st.columns(2)
# Create a line chart of daily addresses
with col1:
    chart_txn = px.line(tx_df, x='Date', y='Transactions', title='Daily Transactions', color_discrete_sequence=['#F7931A'])
    chart_txn.update_layout(yaxis_title='Transactions')
    st.plotly_chart(chart_txn, use_container_width=True)
# Create a line chart of daily transactions
with col2:
    chart_addr = px.line(addr_df, x='Date', y='Addresses', title='Daily Active Addresses', color_discrete_sequence=['#F7931A'])
    chart_addr.update_layout(yaxis_title='Active Addresses')
    st.plotly_chart(chart_addr, use_container_width=True)

st.markdown('<hr />', unsafe_allow_html=True)

# Bitcoin Lightning Network - Title
col1, col2 = st.columns([1, 11])
with col1:
    st.image('https://upload.wikimedia.org/wikipedia/commons/5/5a/Lightning_Network.svg', width=70)
with col2:
    st.header('Bitcoin Lightning Network')
# Bitcoin Lightning Network - Charts
col1, col2 = st.columns(2)
with col1:
    # Create a line chart of daily capacity
    chart_lightning_capacity = px.line(lightning_df, x='Date', y='total_capacity', title='Daily Lightning Capacity', color_discrete_sequence=['#F7931A'])
    chart_lightning_capacity.update_layout(
        yaxis_title='Capacity (BTC)',
        font=dict(size=12),
        title=dict(font=dict(size=16))
    )
    st.plotly_chart(chart_lightning_capacity, use_container_width=True)    
with col2:
    # Create a line chart of daily nodes
    chart_lightning_nodes = px.line(lightning_df, x='Date', y='active_nodes', title='Daily Lightning Node Count', color_discrete_sequence=['#F7931A'])
    chart_lightning_nodes.update_layout(
        yaxis_title='Nodes',
        font=dict(size=12),
        title=dict(font=dict(size=16))
    )
    st.plotly_chart(chart_lightning_nodes, use_container_width=True)

st.markdown('<hr />', unsafe_allow_html=True)

# Bitcoin NFTs - Title
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
    chart_nfts_created.update_layout(yaxis_title='NFT Count')
    st.plotly_chart(chart_nfts_created, use_container_width=True)
with col2:
    # Create a line chart of daily nodes
    chart_nfts_sold = px.bar(nfts_sold_df, x='Date', y='total_sales_usd', color='marketplace', barmode='stack', title='Daily NFTs Sales ($USD)')
    chart_nfts_sold.update_layout(yaxis_title='Sales ($USD)')
    st.plotly_chart(chart_nfts_sold, use_container_width=True)

st.markdown('<hr />', unsafe_allow_html=True)


# Bitcoin Maps - Title
col1, col2 = st.columns([1, 11])
with col1:
    st.image('https://btcmap.org/images/logo.svg', width=70)
with col2:
    st.header("Bitcoin Maps")

st.markdown("""
<iframe
	id="btcmap"
	title="BTC Map"
	width="100%"
	height="500"
	allowfullscreen="true"
	allow="geolocation"
	src="https://btcmap.org/map"
>
</iframe>
""", unsafe_allow_html=True)

