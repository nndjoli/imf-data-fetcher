import httpx
import pandas as pd

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://data.imf.org",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "x-dissemination-channel": "Portals",
}


def datasets():

    datasets = []

    url = "https://data.imf.org/platform/rest/v1/registry/sdmx-plus/structure/dataflow/all/all/latest?detail=full&references=none"
    response = httpx.get(url)
    response.raise_for_status()
    json_reponse = response.json()
    data = json_reponse["data"]
    dataflows = data["dataflows"]

    for i in range(len(dataflows)):

        id = dataflows[i].get("id", None)
        name = dataflows[i].get("name", None)
        description = dataflows[i].get("description", None)
        version = dataflows[i].get("version", None)
        agency_id = dataflows[i].get("agencyID", None)

        dataflow = {
            "id": id,
            "name": name,
            "description": description,
            "version": version,
            "agency_id": agency_id,
        }

        datasets.append(dataflow)

    return pd.DataFrame(datasets)


def dataflow_details(dataset_id):

    ds = datasets()

    if dataset_id not in ds["id"].values:
        raise ValueError(
            f"Dataset ID '{dataset_id}' not found in available datasets. Must be one of: {ds['id'].tolist()}"
        )

    dataset = ds.loc[ds["id"] == dataset_id]
    agency_id = dataset["agency_id"].values[0]
    version = dataset["version"].values[0]

    url = f"https://data.imf.org/platform/rest/v1/registry/sdmx-plus/structure/dataflow/{agency_id}/{dataset_id}/{version}?detail=full&references=descendants"
    response = httpx.get(url, headers=HEADERS)
    response.raise_for_status()
    json_response = response.json()

    terms = []

    glossaries = json_response["data"]["glossaries"]
    for i in range(len(glossaries)):
        glossary = glossaries[i]
        glossary_id = glossary.get("id", None)
        glossary_name = glossary.get("name", None)
        glossary_description = glossary.get("description", None)
        glossary_version = glossary.get("version", None)
        glossary_agency_id = glossary.get("agencyID", None)
        glossary_terms = glossary.get("terms", [])

        if glossary_terms != []:
            for term in glossary_terms:
                term_id = term.get("id", None)
                term_name = term.get("name", None)
                term_description = term.get("description", None)

                terms.append(
                    {
                        "GlossaryID": glossary_id,
                        "GlossaryName": glossary_name,
                        "GlossaryDescription": glossary_description,
                        "GlossaryVersion": glossary_version,
                        "GlossaryAgencyID": glossary_agency_id,
                        "TermID": term_id,
                        "TermName": term_name,
                        "TermDescription": term_description,
                    }
                )

    return pd.DataFrame(terms)


def data_availability(dataset_id):

    ds = datasets()
    if dataset_id not in ds["id"].values:
        raise ValueError(
            f"Dataset ID '{dataset_id}' not found in available datasets. Must be one of: {ds['id'].tolist()}"
        )

    dataset = ds.loc[ds["id"] == dataset_id]
    agency_id = dataset["agency_id"].values[0]
    version = dataset["version"].values[0]

    url = f"https://data.imf.org/platform/rest/v1/registry/sdmx/3.0/availability/dataflow/{agency_id}/{dataset_id}/{version}"

    json_data = {
        "key": "*.*.*.*.*",
        "mode": "available",
        "references": "none",
        "filters": [],
    }

    response = httpx.post(url, headers=HEADERS, json=json_data)
    response.raise_for_status()
    json_response = response.json()

    available_parameters = []

    components = json_response["data"]["dataConstraints"][0]["cubeRegions"]

    for component in range(len(components)):
        comp_container = components[component]["memberSelection"]
        for i in range(len(comp_container)):
            element = comp_container[i]
            element_id = element["componentId"]
            element_selection_values = element["selectionValues"]
            element_values = [
                dictionary["memberValue"]
                for dictionary in element_selection_values
            ]
            for value in element_values:
                available_parameters.append(
                    {
                        "DatasetID": dataset_id,
                        "AgencyID": agency_id,
                        "Version": version,
                        "ComponentID": element_id,
                        "ComponentValue": value,
                    }
                )

    available_parameters = pd.DataFrame(available_parameters)

    return available_parameters


def dataset_query_parameters(dataset_id):

    cur_dflow_det = dataflow_details(dataset_id)
    dset_availability = data_availability(dataset_id)

    curr_dflow_det_copy = dset_availability.copy()
    curr_dflow_det_copy["ComponentID"] = (
        "CL_" + curr_dflow_det_copy["ComponentID"]
    )

    unique_pairs = curr_dflow_det_copy[
        ["ComponentID", "ComponentValue"]
    ].drop_duplicates()

    curr_dflow_det2 = cur_dflow_det[
        cur_dflow_det["GlossaryID"].isin(unique_pairs["ComponentID"])
        & cur_dflow_det["TermID"].isin(unique_pairs["ComponentValue"])
    ][["GlossaryID", "TermID", "TermName", "TermDescription"]].rename(
        columns={
            "GlossaryID": "ComponentID",
            "TermID": "ComponentValue",
            "TermName": "ComponentName",
            "TermDescription": "ComponentDescription",
        }
    )

    curr_dflow_det_copy = curr_dflow_det_copy.merge(
        curr_dflow_det2, on=["ComponentID", "ComponentValue"], how="left"
    )

    curr_dflow_det_copy["ComponentID"] = curr_dflow_det_copy[
        "ComponentID"
    ].str.replace("CL_", "")

    return curr_dflow_det_copy


def build_query_parameters(params_list):
    """
    Convert a list of tuples into a list of dictionaries with specific keys.
    Each tuple should contain three elements: component_code, operator, and value.

    Example input:
    params_list = [
        ('TIME_PERIOD', 'ge', '0'),
        ('COUNTRY', 'eq', 'FRA'),
        ('INDEX_TYPE', 'eq', 'CPI'),
        ('COICOP_1999', 'eq', '_T'),
        ('TYPE_OF_TRANSFORMATION', 'eq', 'IX'),
        ('FREQUENCY', 'eq', 'M')
    ]

    """

    for i, (component_code, operator, value) in enumerate(params_list):
        params_list[i] = {
            "componentCode": component_code,
            "operator": operator,
            "value": value,
        }

    return params_list


def query_indicator(dataset_id, params_list):

    dsets = datasets()

    if dataset_id not in dsets["id"].values:
        raise ValueError(
            f"Dataset ID '{dataset_id}' not found in available datasets. Must be one of: {dsets['id'].tolist()}"
        )

    dataset = dsets.loc[dsets["id"] == dataset_id]
    agency_id = dataset["agency_id"].values[0]
    version = dataset["version"].values[0]

    if not params_list:
        raise ValueError("params_list must contain at least one parameter.")
    if not isinstance(params_list, list):
        raise TypeError("params_list must be a list of tuples.")

    json_data = {
        "agencyID": agency_id,
        "resourceID": dataset_id,
        "version": version,
        "filters": build_query_parameters(params_list),
        "detail": "full",
        "includeHistory": "false",
        "messageVersion": "2.0.0",
        "limit": 1000,
        "attributes": "all",
        "_type": "SdmxDataQueryV3",
    }

    response = httpx.post(
        "https://data.imf.org/platform/rest/v1/registry/sdmx/3.0/dataflow",
        headers=HEADERS,
        json=json_data,
    )
    print(response.url)
    rep = response.json()
    data = rep["data"]["dataSets"][0]["series"]["0:0:0:0:0"]["observations"]
    df_values = pd.DataFrame.from_dict(data, orient="index")
    df_values = df_values.iloc[:, :1]
    df_values.columns = ["Value"]

    dimensions = rep["data"]["structures"][0]["dimensions"]["observation"][0][
        "values"
    ]
    df_dimensions = pd.DataFrame(dimensions, columns=["value"])
    df_dimensions.index = df_values.index
    df_values["Date"] = df_dimensions["value"]
    df_values = df_values[["Date", "Value"]]

    return df_values
