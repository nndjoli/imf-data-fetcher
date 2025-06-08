import nest_asyncio

nest_asyncio.apply()
import asyncio
import httpx
import re
import pandas as pd

from .consts import *


def get_all_dataflows() -> pd.DataFrame:

    url = f"{BASE}/structure/dataflow/?structureType=dataflow&agencyID=%2A&resourceID=%2A&version=%2A&itemID=%2A&detail=full&references=none"

    response = httpx.get(url, headers=HEADERS)
    dataflows = response.json()["data"]["dataflows"]

    results = []
    for flow in dataflows:
        structure_urn = flow.get("structure")
        structure_agency_id, structure_id, structure_version = None, None, None

        if structure_urn:
            match = re.search(r"DataStructure=(.*?):(.*?)\((.*?)\)", structure_urn)
            if match:
                structure_agency_id, structure_id, structure_version = match.groups()

        results.append(
            {
                "DataflowID": flow["id"],
                "DataflowName": flow.get("name"),
                "DataflowVersion": flow.get("version"),
                "DataflowAgencyID": flow.get("agencyID"),
                "StructureID": structure_id,
                "StructureVersion": structure_version,
                "StructureAgencyID": structure_agency_id,
            }
        )

    return pd.DataFrame(results)


def extract_dimensions(dims_json: dict) -> list[dict]:

    dims_raw = dims_json["data"]["dataStructures"][0]["dataStructureComponents"]["dimensionList"]["dimensions"]

    pattern = re.compile(r"Concept=(.*?):(.*?)\((.*?)\)\.(.*)")
    dims = []

    for d in dims_raw:
        m = pattern.search(d.get("conceptIdentity", ""))
        if not m:
            raise ValueError(f"Identité de concept invalide : {d.get('conceptIdentity')}")
        dims.append(
            {
                "ConceptAgencyID": m.group(1),
                "ConceptScheme": m.group(2),
                "ConceptID": m.group(4),
                "CodelistAgencyID": None,
                "CodelistID": None,
            }
        )

    return dims


def associate_codelists(dims, detail_results) -> list[dict]:

    pattern = re.compile(r"Codelist=(.*?):(.*?)\(")

    for i, res in enumerate(detail_results):
        d = dims[i]
        if isinstance(res, Exception):
            continue

        concepts = res["data"]["conceptSchemes"][0]["concepts"]
        concept = next(c for c in concepts if c["id"] == d["ConceptID"])

        enum = concept.get("coreRepresentation", {}).get("enumeration")
        if not enum:
            continue

        m = pattern.search(enum)
        if m:
            d["CodelistAgencyID"], d["CodelistID"] = m.groups()

    return dims


async def query(client, url) -> dict:

    r = await client.get(url)
    if r.status_code == 200:
        return r.json()
    raise httpx.HTTPStatusError(f"GET {url} – {r.status_code}", request=r.request, response=r)


async def queries(dataflow_dict) -> dict:

    async with httpx.AsyncClient(headers=HEADERS, http2=True, timeout=30.0, limits=httpx.Limits(max_connections=20, max_keepalive_connections=20)) as client:

        # Dimensions:
        dim_url = f"{BASE}/structure/datastructure/{dataflow_dict['StructureAgencyID']}/{dataflow_dict['StructureID']}/+"
        dims_json = await query(client, dim_url)
        dims = extract_dimensions(dims_json)

        # Details:
        detail_tasks = {f"detail_{d['ConceptID']}": query(client, f"{BASE}/structure/conceptscheme/{d['ConceptAgencyID']}/{d['ConceptScheme']}/+") for d in dims}
        detail_results = await asyncio.gather(*detail_tasks.values(), return_exceptions=True)

        # Associate codelists:
        dims = associate_codelists(dims, detail_results)

        # Codelists:
        code_tasks = {f"codelist_{d['CodelistID']}": query(client, f"{BASE}/structure/codelist/{d['CodelistAgencyID']}/{d['CodelistID']}/+") for d in dims if d["CodelistID"]}
        code_results = await asyncio.gather(*code_tasks.values(), return_exceptions=True)

        # Availability:
        star_key = ".".join(["*"] * len(dims))
        avail_url = f"{BASE}/availability/dataflow/" f"{dataflow_dict['DataflowAgencyID']}/{dataflow_dict['DataflowID']}" f"/+/{star_key}/all?mode=available"
        availability = await query(client, avail_url)

        # Construct output:
        output = {"dimensions": dims_json, "dimension_details": dict(zip(detail_tasks, detail_results)), "codelists": dict(zip(code_tasks, code_results)), "availability": availability}

        return output


def query_data(agency_id, resource_id, key) -> dict:

    url = f"{BASE}/data/dataflow/{agency_id}/{resource_id}/+/{key}"

    response = httpx.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Error: {response.status_code} {response.reason_phrase}")
        print(response.text)
        return {}

    data = response.json()
    return data
