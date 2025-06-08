import pandas as pd
import re


def process_dataflow_dimensions(response) -> pd.DataFrame:
    dims_json = response["dimensions"]["data"]["dataStructures"][0]["dataStructureComponents"]["dimensionList"]["dimensions"]
    rows = []

    for dim in dims_json:
        urn = dim.get("conceptIdentity", "")
        m = re.search(r"Concept=(.*?):(.*?)\((.*?)\)\.(.*)", urn)
        agency, scheme, version, cid = m.groups() if m else (None,) * 4
        rows.append(
            {
                "ConceptID": cid,
                "ConceptAgencyID": agency,
                "ConceptScheme": scheme,
                "ConceptVersion": version,
                "ConceptPosition": dim.get("position"),
                "ConceptName": dim.get("name", {}).get("en", dim.get("id")),
            }
        )

    df = pd.DataFrame(rows)

    details = response["dimension_details"]
    pattern = re.compile(r"Codelist=(.*?):(.*?)\((.*?)\)")

    for i, row in df.iterrows():
        key = f"detail_{row['ConceptID']}"
        res = details.get(key, {})
        if isinstance(res, Exception) or not res.get("data"):
            df.at[i, "DimensionName"] = None
            df.at[i, "DimensionDescription"] = None
            df.at[i, "CodelistAgencyID"] = None
            df.at[i, "CodelistID"] = None
            df.at[i, "CodelistVersion"] = None
            continue

        concept = next(c for c in res["data"]["conceptSchemes"][0]["concepts"] if c.get("id") == row["ConceptID"])

        nf = concept.get("name", row["ConceptID"])
        df.at[i, "DimensionName"] = nf.get("en") if isinstance(nf, dict) else nf

        df.at[i, "DimensionDescription"] = concept.get("description", {}).get("en", "") if isinstance(concept.get("description"), dict) else concept.get("description", "")

        enum = concept.get("coreRepresentation", {}).get("enumeration")
        if enum:
            m2 = pattern.search(enum)
            if m2:
                df.at[i, "CodelistAgencyID"] = m2.group(1)
                df.at[i, "CodelistID"] = m2.group(2)
                df.at[i, "CodelistVersion"] = m2.group(3)
            else:
                df.at[i, "CodelistAgencyID"] = None
                df.at[i, "CodelistID"] = None
                df.at[i, "CodelistVersion"] = None
        else:
            df.at[i, "CodelistAgencyID"] = None
            df.at[i, "CodelistID"] = None
            df.at[i, "CodelistVersion"] = None

    return df


def process_dimension_details(response, dimensions_dataframe: pd.DataFrame) -> pd.DataFrame:
    details = response["dimension_details"]
    dimensions_dataframe["CodelistAgencyID"] = None
    dimensions_dataframe["CodelistID"] = None

    for idx, row in dimensions_dataframe.iterrows():
        key = f"detail_{row['ConceptID']}"
        res = details.get(key)
        if isinstance(res, Exception):
            continue
        concepts = res["data"]["conceptSchemes"][0]["concepts"]
        concept = next(c for c in concepts if c["id"] == row["ConceptID"])
        enum = concept.get("coreRepresentation", {}).get("enumeration")
        if not enum:
            continue
        m = re.search(r"Codelist=(.*?):(.*?)\(", enum)
        if m:
            dimensions_dataframe.at[idx, "CodelistAgencyID"] = m.group(1)
            dimensions_dataframe.at[idx, "CodelistID"] = m.group(2)
    return dimensions_dataframe


def process_codelists(response, dimensions_dataframe: pd.DataFrame) -> dict:
    codelists = {}
    for _, row in dimensions_dataframe.iterrows():
        dim = row["ConceptID"]
        cl_id = row["CodelistID"]
        key = f"codelist_{cl_id}"
        blob = response["codelists"].get(key)
        if not blob or isinstance(blob, Exception):
            codelists[dim] = []
            continue

        codes = blob["data"]["codelists"][0]["codes"]
        values = []
        for code in codes:
            nf = code.get("name", code.get("id"))
            if isinstance(nf, dict):
                Name = nf.get("en", code["id"])
            else:
                Name = nf
            values.append({"ID": code["id"], "Name": Name})
        codelists[dim] = values
    return codelists


def process_availability(response, codelists_dicts: dict) -> tuple[pd.DataFrame, dict]:
    comp = response["availability"]["data"]["dataConstraints"][0]["cubeRegions"][0]["components"]
    df = pd.json_normalize(comp).rename(columns={"id": "DimensionID"})
    df = df.explode("values").reset_index(drop=True)
    df["Value"] = df["values"].apply(lambda x: x.get("value") if isinstance(x, dict) else None)
    df = df.drop(columns=["include", "removePrefix", "values"])

    def lookup_name(row):
        for item in codelists_dicts.get(row["DimensionID"], []):
            if item["ID"] == row["Value"]:
                return item["Name"]
        return None

    df["Name"] = df.apply(lookup_name, axis=1)  # type: ignore

    avail_dict = {dim: grp.rename(columns={"Value": "ID"})[["ID", "Name"]].to_dict("records") for dim, grp in df.groupby("DimensionID")}
    return df, avail_dict


def process_queried_data(data) -> dict:
    struct = data["data"]["structures"][0]
    dim_series = struct["dimensions"]["series"]
    series_dims = [d["id"] for d in dim_series]
    series_values = {d["id"]: [v["id"] for v in d["values"]] for d in dim_series}

    entity_dim = series_dims[0]
    indicator_dims = series_dims[1:]

    dim_obs = struct["dimensions"]["observation"][0]
    time_values = [v["value"] for v in dim_obs["values"]]

    series_data = data["data"]["dataSets"][0]["series"]
    records = []

    for series_key, series_obj in series_data.items():
        idxs = list(map(int, series_key.split(":")))
        entry = {series_dims[i]: series_values[series_dims[i]][idxs[i]] for i in range(len(idxs))}

        entity = entry[entity_dim]
        if indicator_dims:
            indic_parts = [entry[dim] for dim in indicator_dims]
            Indicator = "_".join(indic_parts)
        else:
            Indicator = entity_dim

        for obs_idx, obs_vals in series_obj["observations"].items():
            obs_idx = int(obs_idx)
            val = obs_vals[0]

            if obs_idx < len(time_values):
                date_str = time_values[obs_idx]
            else:
                date_str = None

            if date_str is None:
                date = pd.NaT
            elif re.fullmatch(r"\d{4}", date_str):
                date = pd.to_datetime(date_str, format="%Y")
            elif re.fullmatch(r"\d{4}-M\d{2}", date_str):
                date = pd.to_datetime(date_str.replace("M", ""), format="%Y-%m")
            elif re.fullmatch(r"\d{4}-Q[1-4]", date_str):
                year, q = date_str.split("-Q")
                mois_par_quarter = {"1": "01", "2": "04", "3": "07", "4": "10"}
                month = mois_par_quarter[q]
                date = pd.to_datetime(f"{year}-{month}", format="%Y-%m")
            else:
                date = pd.to_datetime(date_str, errors="coerce")

            records.append(
                {
                    entity_dim: entity,
                    "Indicator": Indicator,
                    "Date": date,
                    "Value": float(val) if val is not None else None,
                }
            )

    df_all = pd.DataFrame(records)

    dfs = {}
    for indic in df_all["Indicator"].unique():
        df_ind = df_all[df_all["Indicator"] == indic].copy()
        df_pivot = df_ind.pivot(index="Date", columns=entity_dim, values="Value")
        df_pivot.index.name = "Date"
        dfs[indic] = df_pivot

    return dfs
