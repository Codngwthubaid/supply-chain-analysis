import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import matplotlib.ticker as ticker
import matplotlib.cm as cm
from IPython.display import display
from warnings import filterwarnings
filterwarnings('ignore')


# Set a professional color theme for visuals
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("viridis")

viridis_colors = cm.viridis(np.linspace(0, 1, 5))
primary_color = viridis_colors[0]
secondary_color = viridis_colors[1]
accent_color = viridis_colors[2]
danger_color = '#800000'
neutral_color = viridis_colors[4]
custom_palette = viridis_colors


# reading csv files
df = pd.read_csv('data/DataCoSupplyChainDataset.csv', encoding = 'latin-1')


# overview
# display('Before Cleaning Dataset : rows, cols : ', df.shape)
# print('\n columns')
# display(df.columns.tolist())
# print('\n Num of duplicates :', df.duplicated().sum())
# print('\n Num of missing values (top 20):')
# display(df.isna().sum().sort_values(ascending=False).head(20))


# checking similar cols : we can remove one col because both col vals are same
# display(df['Benefit per order'] == df['Order Profit Per Order'])

# data cleaning - this entire list contains values that we do not need for our analysis
columns_to_drop_from_dataset = [
    'Product Description',
    'Product Image',
    'Product Card Id',
    'Product Category Id',
    'Product Status',
    'Customer Email',
    'Customer Password',
    'Customer Fname',
    'Customer Lname',
    'Customer Street',
    'Customer Zipcode',
    'Customer State',
    'Customer City',
    'Customer Id',
    'Longitude',
    'Latitude',
    'Order Item Cardprod Id',
    'Order Item Id',
    'Order Item Discount',
    'Order Item Discount Rate',
    'Order Item Product Price',
    'Order Item Quantity',
    'Order Item Total',
    'Order Id',
    'Order Zipcode',
    'Order Customer Id',
    'Order City', 
    'Order State',
    'Order Country',
    'Category Id',
    'Market',
    'Department Id',
    'Benefit per order'
]

df = df.drop(columns=columns_to_drop_from_dataset)

# removing all cancelled orders hence it doesnot effect our analysis
df = df[df['Delivery Status'] != 'Shipping canceled']

# convert dtype of cols : "shipping date (DateOrders)", "order date (DateOrders)" currently present in STR --> DATETIME
for col in ['shipping date (DateOrders)', 'order date (DateOrders)']:
    df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=False)

# after cleaning data now let's, check how our dataset looks 
# print('After Cleaning Dataset : rows, cols : ', df.shape)
# print('\nMissing values (top 5) :')
# display(df.isna().sum().sort_values(ascending=False).head(5))


# count values for categorical cols with less than 10 variety
# for col in df.columns:
#     if df[col].nunique() <= 10:
        # display(f'\n {col} : {df[col].nunique()} unique values')
        # display(df[col].value_counts())


# calculating the order processing time and delay - by creating new cols of order :
# Order Processing Time, 
# Delay, 
# Is_Delayed, 
# order_month, 
# order_day, 
# order_hour

df['Order Processing Time'] = (df['shipping date (DateOrders)'] - df['order date (DateOrders)']).dt.days
df['Delay'] = (df['Order Processing Time'] - df['Days for shipment (scheduled)'])
df['Is_Delayed'] = df['Delay'] > 0
df['order_month'] = df['order date (DateOrders)'].dt.month
df['order_day'] = df['order date (DateOrders)'].dt.day
df['order_hour'] = df['order date (DateOrders)'].dt.hour

# display(df.describe().T)
# display(df['Order Profit Per Order'])

# now, first we check the profitability of the company, then we again calculate the profitability with respect to Order Processing Time and Delay that how these effect our company profitability

# now, creating a new col which tell us the profitability flag i.e profit, loss orr break-even
df['Profitability Flag'] = np.where(
    df['Order Profit Per Order'] > 0, "Profit",
    np.where(
        df['Order Profit Per Order'] < 0, 'Loss',
        "Break-even"
        )
)
# display(df['Profitability Flag'].value_counts())

# create a pie chat for visualization of profitability distribution
profit_counts = df['Profitability Flag'].value_counts(normalize = True) * 100
# profit_counts.plot(kind = 'pie', 
#     autopct = '%1.1f%%', 
#     startangle = 90, 
#     figsize = (8, 8), 
#     colors = [accent_color, danger_color, secondary_color],
#     wedgeprops = {'edgecolor': 'black', 'linewidth': 1})

# plt.title('Profitability Distribution (%)')
# plt.savefig('figures/profitability_distribution.png', dpi = 300, bbox_inches = 'tight')
# plt.show()


# now, figure out the key performance KPI's such as : 
# total_orders, 
# late_deliveries, 
# late_delivery_percent, 
# on_time_deliary_percent, 
# total_profit(profitable orders), 
# profit_at_risk(delayed_orders), 
# avg_order_profit, 
# 90th_percentile_delay

# helper function 
def format_func(value):
    if value >= 1e6:
        return f'${value*1e-6:.1f}M'
    elif value >= 1e3:
        return f'${value*1e-3:.1f}K'
    else:
        return f'${value:.0f}'


# creating a new df of only delayed orders
delayed_df = df[df['Delay'] > 0]
metrics = {}
metrics['Total Orders'] = len(df)
metrics['Late Deliveries'] = len(delayed_df)
metrics['90% Delay (days)'] = delayed_df['Delay'].quantile(0.90)
metrics['On time delivery %'] = (1 - float(metrics['Late Deliveries']) / metrics['Total Orders']) * 100
metrics['Late delivery %'] = (float(metrics['Late Deliveries']) / metrics['Total Orders']) * 100
metrics['Total profit'] = format_func(df.loc[df['Order Profit Per Order'] > 0, 'Order Profit Per Order'].sum())
metrics['Total loss due to delay'] = format_func(df.loc[df['Delay'] > 0, 'Order Profit Per Order'].sum())

# print("\n --- Business KPI's --- \n")
# for key, value in metrics.items():
#     if isinstance(value, float):
#         print(f'{key} : {value:.2f}')
#     else:
#         print(f'{key} : {value}')


# now, we find out the profitability VS delivery time analysis
profit_metrics = (
    df.groupby('Delay')['Order Profit Per Order'].agg(
        mean_profit='mean',
        total_profit='sum',
        order_count='count'
    ).reset_index()
)

# some deliveries are delay by 2-4 days and some deliveries are before time but the mean_profit is same ~22
# print(profit_metrics.head(10))


# now, finding out the delay distribution
delay_distribution = (
    df['Delay'].value_counts(normalize=True).sort_values()*100
).reset_index()

# delivery late by 3 days have 3.91% and by 4 days have 3.87% and 0 days have 21.21%
# print(delay_distribution)


# now, create a visualization for delay_distribution
# delay_distribution.columns = ['Delay_Days', 'Percentage']

# print('\nProfit Metrics by Delay Days :')
# display(profit_metrics.round(1))

# print('\nDelay Distribution :')
# display(delay_distribution.round(1))

# fig, (ax1,ax2) = plt.subplots(1,2,figsize=(16,6))

# first subplot: delay distribution
# sns.barplot(x="Delay_Days", y="Percentage", data=delay_distribution, color=accent_color,ax=ax1)
# ax1.set_title('Delay Distribution')
# ax1.set_xlabel('Delay (Days)')
# ax1.set_ylabel('percentage of orders (%)')


# second subplot : profit analysis by delay distribution
# ax2.set_ylabel("Total Profit", color=primary_color)
# ax2.bar(profit_metrics['Delay'], profit_metrics['total_profit'], color=primary_color, label="Total Profit")
# ax2.tick_params(axis='y',labelcolor=primary_color)

# ax3 = ax2.twinx()

# ax3.set_xlabel("Delay Days")
# ax3.set_ylabel("Mean Profit", color=accent_color)
# ax3.plot(
#     profit_metrics['Delay'], 
#     profit_metrics['mean_profit'], 
#     color = accent_color, 
#     marker='o',
#     label="Mean Profit"
# )
# ax3.tick_params(axis='y', labelcolor=accent_color)

# helper format function 
def format_fun(value,tick_number):
    if value >= 1e6:
        return f'${value*1e-6:.1f}M'
    elif value >= 1e3:
        return f'${value*1e-3:.1f}K'
    else:
        return f'${value:.0f}'

# ax2.yaxis.set_major_formatter(ticker.FuncFormatter(format_fun))

# lines, labels = ax3.get_legend_handles_labels()
# lines2, labels2 = ax2.get_legend_handles_labels()


# ax3.legend(lines+lines2, labels+labels2, loc = 'upper right')
# ax3.grid(True, linestyle=':', alpha=0.5)
# plt.title('Profit Analysis by Delay Days')
# plt.savefig('figures/profit_analysis_by_delay.png', dpi=300, bbox_inches='tight')
# plt.tight_layout()
# plt.show()


# now, let's do the bottleneck detection

def compute_delay_percentage_by_category(category):
    category_df = df.groupby(category).agg(
        total_orders = ('Delay', 'count'),
        late_orders = ('Is_Delayed', 'sum')
    ).reset_index()
    category_df['delay_percent'] = (category_df['late_orders'] / category_df['total_orders']) * 100
    category_df = category_df.sort_values('delay_percent', ascending=False).head(10)
    return category_df

# setting custom categories from dataset columns
categories = [
    'Order Region',
    'Customer Segment',
    'Shipping0 Mode',
    'Order Status',
    'Type',
    'Department Name'
]

fig, axes = plt.subplots(2,3, figsize=(16,7), constrained_layout=True)
axes = axes.flatten()

for ax, category in zip(axes, categories):
    category_df = compute_delay_percentage_by_category(category)
    sns.barplot(
        data=category_df,
        x='delay_percent',
        y=category,
        ax=ax,
        palette='viridis'
    )
    ax.set_title(f'Delay Percentage by {category}', fontsize=10)
    ax.set_xlabel('')
    ax.set_ylabel(category)
    for i, row in category_df.reset_index().iterrows():
        ax.text(
            row['delay_percent'] - 15,
            i, 
            f"{row['delay_percent']:.1f}%", 
            va='center', 
            fontsize=10, 
            color='white'
        )

plt.savefig('figures/delay_percentage_by_category.png', dpi=300, bbox_inches='tight')
plt.show()
    