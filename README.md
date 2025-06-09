<h1>imf_data_fetcher</h1>

Interacts with the International Monetary Fund API (SDMX 3.0) to retrieve macroeconomic data.

<h2>Requirements & Installation:</h2>

* **Dependencies**: `httpx`, `pandas`, `nest_asyncio`
* **To install**, run:

  ```bash
  pip install imf-data-fetcher==0.1
  ```

<h2>Example:</h2>

An `IMFInstance` is the entry point for accessing IMF datasets:

```python
import imf_data_fetcher

# Create an instance of IMFInstance:
instance = imf_data_fetcher.IMFInstance()
# <IMFInstance object>
```

Each dataset provided by the IMF (e.g., CPI, National Economic Accounts, World Economic Outlook) is represented by a distinct dataflow. You can list available dataflows via the `dataflows` attribute:

```python
# List available dataflows:
dataflows = instance.dataflows
```

| DataflowID | DataflowName                                        | DataflowVersion | DataflowAgencyID | StructureID  | StructureVersion | StructureAgencyID |
| ---------- | --------------------------------------------------- | --------------- | ---------------- | ------------ | ---------------- | ----------------- |
| FD         | Fiscal Decentralization (FD)                        | 6.0.0           | IMF.STA          | DSD\_FD      | 6.0+.0           | IMF.STA           |
| CPI        | Consumer Price Index (CPI)                          | 3.0.1           | IMF.STA          | DSD\_CPI     | 3.0+.0           | IMF.STA           |
| FAS        | Financial Access Survey (FAS)                       | 4.0.0           | IMF.STA          | DSD\_FAS     | 4.0+.0           | IMF.STA           |
| ER         | Exchange Rates (ER)                                 | 4.0.1           | IMF.STA          | DSD\_ER\_PUB | 4.0+.0           | IMF.STA           |
| ...        | ...                                                 | ...             | ...              | ...          | ...              | ...               |
| ITG        | International Trade in Goods (ITG)                  | 4.0.0           | IMF.STA          | DSD\_ITG     | 4.0+.0           | IMF.STA           |
| ANEA       | National Economic Accounts (NEA), Annual Data       | 6.0.1           | IMF.STA          | DSD\_ANEA    | 8.0+.0           | IMF.STA           |
| APDREO     | Asia and Pacific Regional Economic Outlook (APDREO) | 6.0.0           | IMF.APD          | DSD\_APDREO  | 6.0+.0           | IMF.APD           |
| WEO        | World Economic Outlook (WEO)                        | 6.0.0           | IMF.RES          | DSD\_WEO     | 6.0+.0           | IMF.RES           |

Once you’ve chosen a dataflow, initialize a `Dataflow` object:

```python
# Select the Consumer Price Index (CPI) dataflow:
dataflow = instance.Dataflow('CPI')
# <Dataflow object>
```

This object exposes all relevant metadata, including available dimensions (e.g., country, index type, frequency) for refining queries. Retrieve dimensions via:

```python
# Get dimensions metadata:
dimensions = dataflow.dimensions
```

| ConceptID | ConceptAgencyID | ConceptScheme      | ConceptVersion | ConceptPosition | ConceptName              | DimensionName        | DimensionDescription                                                                  | CodelistAgencyID | CodelistID                        | CodelistVersion |
| --------- | --------------- | ------------------ | -------------- | --------------- | ------------------------ | -------------------- | ------------------------------------------------------------------------------------- | ---------------- | --------------------------------- | --------------- |
| 0         | IMF             | CS\_MASTER\_DATA   | 1.0+.0         | 0               | COUNTRY                  | Country              | The country or region for which the data are reported                                 | IMF              | CL\_COUNTRY                       | 1.0+.0          |
| 1         | IMF             | CS\_MASTER\_DOMAIN | 1.0+.0         | 1               | INDEX\_TYPE              | Index type           | Type of index prices                                                                  | IMF              | CL\_INDEX\_TYPE                   | 2.0+.0          |
| 2         | IMF             | CS\_MASTER\_DOMAIN | 1.0+.0         | 2               | COICOP\_1999             | Expenditure Category | Classification of Individual Consumption According to Purpose (COICOP), revision 1999 | IMF              | CL\_COICOP\_1999                  | 1.0+.0          |
| 3         | IMF.STA         | CS\_CPI            | 3.0+.0         | 3               | TYPE\_OF\_TRANSFORMATION | Transformation type  | Specific calculations applied to raw price data                                       | IMF.STA          | CL\_CPI\_TYPE\_OF\_TRANSFORMATION | 3.0+.0          |
| 4         | IMF             | CS\_MASTER\_SYSTEM | 1.0+.0         | 4               | FREQ                     | Frequency            | Frequency of the reported data                                                        | IMF              | CL\_FREQ                          | 1.0+.0          |

For each dimension, fetch valid values—use both `dimensions_available_values` (a `pandas.DataFrame`) and `_dimensions_available_values` (a `dict`):

```python
avail = dataflow._dimensions_available_values
```

```python
{
  'COICOP_1999': [
    {'ID': 'CP01', 'Name': 'Food and non-alcoholic beverages'},
    ...
    {'ID': '_T',   'Name': 'All Items'}
  ],
  'COUNTRY': [
    {'ID': 'USA', 'Name': 'United States'},
    {'ID': 'CAN', 'Name': 'Canada'},
    {'ID': 'GBR', 'Name': 'United Kingdom'},
    ...
  ],
  'FREQUENCY': [
    {'ID': 'A', 'Name': None},
    {'ID': 'M', 'Name': None},
    {'ID': 'Q', 'Name': None}
  ],
  'INDEX_TYPE': [
    {'ID': 'CPI',  'Name': 'Consumer Price Index'},
    {'ID': 'HICP', 'Name': 'Harmonised Index of Consumer Prices'}
  ],
  'TYPE_OF_TRANSFORMATION': [
    {'ID': 'IX',          'Name': 'Index'},
    {'ID': 'YOY_PCH_PA_PT','Name': 'Year-over-year percent change'},
    ...
  ]
}
```

Copy and adjust the query template:

```python
# Build query parameters template:
qpar = dataflow.query_params_dict_template.copy()
# {
#   'COUNTRY': '*',
#   'INDEX_TYPE': '*',
#   'COICOP_1999': '*',
#   'TYPE_OF_TRANSFORMATION': '*',
#   'FREQUENCY': '*'
# }
```

Set filters:

```python
qpar['COUNTRY']              = ['USA', 'CAN', 'GBR']  # United States, Canada, United Kingdom
qpar['INDEX_TYPE']           = 'CPI'                   # Consumer Price Index
qpar['COICOP_1999']          = '_T'                    # All items
qpar['TYPE_OF_TRANSFORMATION']= 'IX'                    # Index transformation
qpar['FREQUENCY']            = 'M'                     # Monthly frequency
```

Execute the query and clean results:

```python
data = dataflow.query(qpar).dropna()
```

| Date       | CAN   | GBR      | USA       |
| ---------- | ----- | -------- | --------- |
| 1955-01-01 | 14.1  | 4.859513 | 12.244589 |
| ...        | ...   | ...      | ...       |
| 2025-04-01 | 163.4 | 137.700  | 147.116   |

*Shape: 844 rows × 3 columns*

**Note:** If the IMF API returns multiple tables, the `query` method outputs a `dict` of DataFrames, one per table.
