import pandas as pd
pd.set_option('future.no_silent_downcasting', True)

from pytrends.request import TrendReq
py = TrendReq(hl='en-IN', tz=330)
py.build_payload(['Wtflex'], timeframe='today 12-m', geo='IN')
df = py.interest_over_time()

print("Google Trends Data for 'Mamaearth' in India (Last 12 months):")
print("=" * 60)
print(df.head(10))
print("\nData shape:", df.shape)
print("\nColumns:", df.columns.tolist())