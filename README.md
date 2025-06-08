<h1>imf_data_fetcher</h1> 

- Interacts with the International Monetary Fund API (SDMX 3.0) to retrieve macroeconomic data.

<h2>Requirements & Installation :</h2>

- Requirements: `httpx`, `pandas`, `nest_asyncio`.  
- Install using: `pip install imf-data-fetcher==0.1` (https://pypi.org/project/imf-data-fetcher/0.1/)
 


<h2>Example:</h2>


```python
import imf_data_fetcher 

#  Create an instance of IMFInstance:
instance = imf_data_fetcher.IMFInstance()
>>> <IMF.imf_data_fetcher.main.IMFInstance at 0x1a2488a9780>
```

```python
# Check available dataflows:
dataflows = instance.dataflows
```
| DataflowID | DataflowName                                         | DataflowVersion | DataflowAgencyID | StructureID   | StructureVersion | StructureAgencyID |
|------------|------------------------------------------------------|-----------------|------------------|---------------|------------------|-------------------|
| FD         | Fiscal Decentralization (FD)                         | 6.0.0           | IMF.STA          | DSD_FD        | 6.0+.0           | IMF.STA           |
| CPI        | Consumer Price Index (CPI)                           | 3.0.1           | IMF.STA          | DSD_CPI       | 3.0+.0           | IMF.STA           |
| FAS        | Financial Access Survey (FAS)                        | 4.0.0           | IMF.STA          | DSD_FAS       | 4.0+.0           | IMF.STA           |
| ER         | Exchange Rates (ER)                                  | 4.0.1           | IMF.STA          | DSD_ER_PUB    | 4.0+.0           | IMF.STA           |
| ...        | ...                                                  | ...             | ...              | ...           | ...              | ...               |
| ITG        | International Trade in Goods (ITG)                   | 4.0.0           | IMF.STA          | DSD_ITG       | 4.0+.0           | IMF.STA           |
| ANEA       | National Economic Accounts (NEA), Annual Data        | 6.0.1           | IMF.STA          | DSD_ANEA      | 8.0+.0           | IMF.STA           |
| APDREO     | Asia and Pacific Regional Economic Outlook (APDREO)  | 6.0.0           | IMF.APD          | DSD_APDREO    | 6.0+.0           | IMF.APD           |
| WEO        | World Economic Outlook (WEO)                         | 6.0.0           | IMF.RES          | DSD_WEO       | 6.0+.0           | IMF.RES           |

```python
# Set the instance to use the Consumer Price Index (CPI) database:
dataflow = instance.Dataflow('CPI')
>>> <IMF.imf_data_fetcher.main.IMFInstance.DataflowObject at 0x1a2488a9c90>
```

```python
# Check dimensions and their values:
dimensions = dataflow.dimensions
```
| ConceptID | ConceptAgencyID | ConceptScheme      | ConceptVersion | ConceptPosition | ConceptName              | DimensionName          | DimensionDescription                                                                      | CodelistAgencyID | CodelistID                        | CodelistVersion |
| --------- | --------------- | ------------------ | -------------- | --------------- | ------------------------ | ---------------------- | ----------------------------------------------------------------------------------------- | ---------------- | --------------------------------- | --------------- |
| 0         | IMF             | CS\_MASTER\_DATA   | 1.0+.0         | 0               | COUNTRY                  | Country                | The country or region for which the data or series are reported                           | IMF              | CL\_COUNTRY                       | 1.0+.0          |
| 1         | IMF             | CS\_MASTER\_DOMAIN | 1.0+.0         | 1               | INDEX\_TYPE              | Index type             | Type of index prices.                                                                     | IMF              | CL\_INDEX\_TYPE                   | 2.0+.0          |
| 2         | IMF             | CS\_MASTER\_DOMAIN | 1.0+.0         | 2               | COICOP\_1999             | Expenditure Category   | The Classification of Individual Consumption According to Purpose (COICOP), revision 1999 | IMF              | CL\_COICOP\_1999                  | 1.0+.0          |
| 3         | IMF.STA         | CS\_CPI            | 3.0+.0         | 3               | TYPE\_OF\_TRANSFORMATION | Type of Transformation | Represents the specific calculations or computations applied to the raw price data        | IMF.STA          | CL\_CPI\_TYPE\_OF\_TRANSFORMATION | 3.0+.0          |
| 4         | IMF             | CS\_MASTER\_SYSTEM | 1.0+.0         | 4               | FREQ                     | Frequency              |                                                                                           | IMF              | CL\_FREQ                          | 1.0+.0          |


```python
avail = dataflow._dimensions_available_values
>>>
    {'COICOP_1999': [{'ID': 'CP01', 'Name': 'Food and non-alcoholic beverages'},
    {'ID': 'CP02', 'Name': 'Alcoholic beverages, tobacco and narcotics'},
    {'ID': 'CP03', 'Name': 'Clothing and footwear'},
    {'ID': 'CP04', 'Name': 'Housing, water, electricity, gas and other fuels'},
    {'ID': 'CP05',
    'Name': 'Furnishings, household equipment and routine household maintenance'},
    {'ID': 'CP06', 'Name': 'Health'},
    {'ID': 'CP07', 'Name': 'Transport'},
    {'ID': 'CP08', 'Name': 'Communication'},
    {'ID': 'CP09', 'Name': 'Recreation and culture'},
    {'ID': 'CP10', 'Name': 'Education'},
    {'ID': 'CP11', 'Name': 'Restaurants and hotels'},
    {'ID': 'CP12', 'Name': 'Miscellaneous goods and services'},
    {'ID': '_T', 'Name': 'All Items '}],
    'COUNTRY': [{'ID': 'ABW', 'Name': 'Aruba, Kingdom of the Netherlands'},
    {'ID': 'AFG', 'Name': 'Afghanistan, Islamic Republic of'},
    {'ID': 'AGO', 'Name': 'Angola'},
    ...
    {'ID': 'ZMB', 'Name': 'Zambia'},
    {'ID': 'ZWE', 'Name': 'Zimbabwe'}],
    'FREQUENCY': [{'ID': 'A', 'Name': None},
    {'ID': 'M', 'Name': None},
    {'ID': 'Q', 'Name': None}],
    'INDEX_TYPE': [{'ID': 'CPI', 'Name': 'Consumer price index (CPI)'},
    {'ID': 'HICP', 'Name': 'Harmonised index of consumer prices (HICP)'}],
    'TYPE_OF_TRANSFORMATION': [{'ID': 'IX', 'Name': 'Index'},
    {'ID': 'POP_PCH_PA_PT',
    'Name': 'Period average, Period-over-period percent change'},
    {'ID': 'WGT', 'Name': 'Weight'},
    {'ID': 'WGT_PT', 'Name': 'Weight, Percent'},
    {'ID': 'YOY_PCH_PA_PT',
    'Name': 'Period average, Year-over-year (YOY) percent change'}]}
```

```python
# Bulid Query Parameters dictionary:
qpar = dataflow.query_params_dict_template.copy()
>>> {
    'COUNTRY': '*',
    'INDEX_TYPE': '*',
    'COICOP_1999': '*',
    'TYPE_OF_TRANSFORMATION': '*',
    'FREQUENCY': '*'
    }

qpar['COUNTRY'] = ['USA', 'CAN', 'GBR'] # United States, Canada, and Great Britain
qpar['TYPE_OF_TRANSFORMATION'] = 'IX' # Index transformation
qpar['COICOP_1999'] = '_T' # All items 
qpar['INDEX_TYPE'] ='CPI' # Consumer Price Index
qpar['FREQUENCY'] = 'M' # Monthly frequency

# Build the query:
data = dataflow.query(qpar).dropna()
```
| Date       | CAN    | GBR       | USA       |
|------------|--------|-----------|-----------|
| 1955-01-01 | 14.1   | 4.859513  | 12.244589 |
| 1955-02-01 | 14.1   | 4.859513  | 12.244589 |
| 1955-03-01 | 14.1   | 4.859513  | 12.244589 |
| 1955-04-01 | 14.1   | 4.885972  | 12.244589 |
| 1955-05-01 | 14.1   | 4.877152  | 12.244589 |
| ...        | ...    | ...       | ...       |
| 2024-12-01 | 161.2  | 135.100000| 144.736088|
| 2025-01-01 | 161.3  | 135.100000| 145.683553|
| 2025-02-01 | 163.0  | 135.600000| 146.330636|
| 2025-03-01 | 163.5  | 136.100000| 146.659451|
| 2025-04-01 | 163.4  | 137.700000| 147.116216|
| ...        | ...    | ...       | ...       |

*844 rows × 3 columns*

