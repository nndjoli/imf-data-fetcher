import httpx
import pandas as pd


# Build Dataflows DataFrame:
def dataflows_df():

    # Fetching the list of dataflows from the IMF SDMX Plus API
    dataflows_url = "https://data.imf.org/platform/rest/v1/registry/sdmx-plus/structure/dataflow/all/all/latest?detail=full&references=none"
    dataflows_json = httpx.get(dataflows_url).json()

    # Extracting dataflows from the JSON response
    dataflows = dataflows_json["data"]["dataflows"]
    dataflows = [
        {
            "Name": dataflows[i]["name"],
            "ID": dataflows[i]["id"],
            "Description": dataflows[i]["description"],
            "Version": dataflows[i]["version"],
            "AgencyID": dataflows[i]["agencyID"],
            "DataflowURL": dataflows[i]["links"][0]["urn"],
            "StructureURL": dataflows[i]["structure"],
        }
        for i in range(len(dataflows))
    ]

    dataflows_df = pd.DataFrame(dataflows)
    dataflows_df["DataflowURL"] = "https://data.imf.org/platform/rest/v1/registry/sdmx-plus/structure/dataflow/" + dataflows_df["AgencyID"] + "/" + dataflows_df["ID"] + "/" + dataflows_df["Version"] + "?detail=full&references=descendants"
    dataflows_df["StructureURL"] = "https://data.imf.org/platform/rest/v1/registry/sdmx-plus/structure/datastructure/" + dataflows_df["AgencyID"] + "/DSD_" + dataflows_df["ID"] + "/" + dataflows_df["StructureURL"].str.split("(").str[1].str.split(")").str[0] + "?detail=full&references=descendants"
    return dataflows_df


# Extract Dataflow & Data Structure Information:
def extract_concept_schemes(concept_schemes):

    schemes = []

    for i in range(len(concept_schemes)):
        links = concept_schemes[i].get("links", None)
        annotations = concept_schemes[i].get("annotations", None)
        id = concept_schemes[i].get("id", None)
        name = concept_schemes[i].get("name", None)
        names = concept_schemes[i].get("names", None)
        description = concept_schemes[i].get("description", None)
        descriptions = concept_schemes[i].get("descriptions", None)
        version = concept_schemes[i].get("version", None)
        agencyID = concept_schemes[i].get("agencyID", None)
        concepts = concept_schemes[i].get("concepts", None)
        isPartial = concept_schemes[i].get("isPartial", None)

        concepts = [
            {
                "ConceptSchemeID": id,
                "ConceptSchemeName": name,
                "ConceptSchemeVersion": version,
                "ConceptSchemeAgencyID": agencyID,
                "ConceptSchemeDescription": description,
                "ConceptSchemeIsPartial": isPartial,
                "ConceptName": concepts[j].get("name", None),
                "ConceptID": concepts[j].get("id", None),
                "ConceptDescription": concepts[j].get("description", None),
                "ConceptCoreRepresentation": concepts[j].get("coreRepresentation", None),
            }
            for j in range(len(concepts))
        ]

        schemes.append(concepts)

    return schemes


def extract_data_structures(data_structures):

    structures = []

    for i in range(len(data_structures)):
        links = data_structures[i].get("links", None)
        if links is not None:
            links = [link["urn"] for link in links]

        annotations = data_structures[i].get("annotations", None)
        id = data_structures[i].get("id", None)
        name = data_structures[i].get("name", None)
        names = data_structures[i].get("names", None)
        description = data_structures[i].get("description", None)
        descriptions = data_structures[i].get("descriptions", None)
        version = data_structures[i].get("version", None)
        agencyID = data_structures[i].get("agencyID", None)
        data_structure_components = data_structures[i].get("dataStructureComponents", None)

        if data_structure_components is None:
            continue

        attributeList = data_structure_components.get("attributeList", None)

        if attributeList is not None:
            attributeList = [
                {
                    "StructureID": id,
                    "StructureName": name,
                    "StructureVersion": version,
                    "StructureAgencyID": agencyID,
                    "StructureDescription": description,
                    "AttributeID": element.get("id", None),
                    "AttributeURN": element.get("conceptIdentity", None),
                    "AttributeIsMandatory": element.get("isMandatory", None),
                }
                for element in attributeList["attributes"]
            ]

        dimensionList = data_structure_components.get("dimensionList", None)

        if dimensionList is not None:
            dimensionList = [
                {
                    "StructureID": id,
                    "StructureName": name,
                    "StructureVersion": version,
                    "StructureAgencyID": agencyID,
                    "StructureDescription": description,
                    "DimensionID": element.get("id", None),
                    "DimensionURN": element.get("conceptIdentity", None),
                    "DimensionPosition": element.get("position", None),
                }
                for element in (dimensionList.get("dimensions", []) + dimensionList.get("timeDimensions", []))
            ]

        measureList = data_structure_components.get("measureList", None)

        if measureList is not None:
            measureList = [
                {
                    "StructureID": id,
                    "StructureName": name,
                    "StructureVersion": version,
                    "StructureAgencyID": agencyID,
                    "StructureDescription": description,
                    "MeasureID": element.get("id", None),
                    "MeasureURN": element.get("conceptIdentity", None),
                }
                for element in measureList["measures"]
            ]

        metadata = data_structures[i].get("metadata", None)

        structure = {"StructureID": id, "StructureName": name, "StructureVersion": version, "StructureAgencyID": agencyID, "StructureDescription": description, "Links": links, "AttributeList": attributeList, "DimensionList": dimensionList, "MeasureList": measureList, "Metadata": metadata}
        structures.append(structure)

    return structures


def extract_metadata_structures(metadata_structures):

    structures = []

    for i in range(len(metadata_structures)):
        links = metadata_structures[i].get("links", None)
        if links is not None:
            links = [link["urn"] for link in links]

        annotations = metadata_structures[i].get("annotations", None)
        id = metadata_structures[i].get("id", None)
        name = metadata_structures[i].get("name", None)
        names = metadata_structures[i].get("names", None)
        description = metadata_structures[i].get("description", None)
        descriptions = metadata_structures[i].get("descriptions", None)
        version = metadata_structures[i].get("version", None)
        agencyID = metadata_structures[i].get("agencyID", None)

        metadata_structure_components = metadata_structures[i].get("metadataStructureComponents", None)
        if metadata_structure_components is None:
            continue
        metadata_structure_components = metadata_structure_components.get("metadataAttributeList", None)
        if metadata_structure_components is None:
            continue

        attributes = metadata_structure_components.get("metadataAttributes", None)

        if attributes is not None:
            attributes = [
                {
                    "MetadataStructureID": id,
                    "MetadataStructureName": name,
                    "MetadataStructureVersion": version,
                    "MetadataStructureAgencyID": agencyID,
                    "MetadataStructureDescription": description,
                    "AttributeID": element.get("id", None),
                    "AttributeURN": element.get("conceptIdentity", None),
                    "AttributeMaxOccurs": element.get("maxOccurs", None),
                }
                for element in attributes
            ]

    structure = {"MetadataStructureID": id, "MetadataStructureName": name, "MetadataStructureVersion": version, "MetadataStructureAgencyID": agencyID, "MetadataStructureDescription": description, "Links": links, "Attributes": attributes}

    structures.append(structure)

    return structures


def extract_dataflows(dataflows):

    extracted_dataflows = []

    for dataflow in dataflows:
        extracted_dataflow = {
            "DataflowID": dataflow.get("id", None),
            "DataflowName": dataflow.get("name", None),
            "DataflowDescription": dataflow.get("description", None),
            "DataflowVersion": dataflow.get("version", None),
            "DataflowAgencyID": dataflow.get("agencyID", None),
            "Links": [link["urn"] for link in dataflow.get("links", [])],
        }
        extracted_dataflows.append(extracted_dataflow)

    return extracted_dataflows


def extract_glossary(glossaries):

    glossary = []

    for glossary_ in glossaries:
        glossary_name = glossary_.get("name", None)
        glossary_description = glossary_.get("description", None)
        glossary_id = glossary_.get("id", None)
        glossary_version = glossary_.get("version", None)
        glossary_agencyID = glossary_.get("agencyID", None)
        glossary_terms = glossary_.get("terms", None)
        glossary_terms = [
            {
                "GlossaryID": glossary_id,
                "GlossaryName": glossary_name,
                "GlossaryVersion": glossary_version,
                "GlossaryAgencyID": glossary_agencyID,
                "GlossaryDescription": glossary_description,
                "TermID": term.get("id", None),
                "TermName": term.get("name", None),
                "TermDescription": term.get("description", None),
            }
            for term in glossary_terms
        ]

        glossary.extend(glossary_terms)

    return glossary


def dataflow(dataflow_id=None):

    x = dataflows_df()

    if dataflow_id not in x["ID"].values:
        raise ValueError(f"Dataflow ID '{dataflow_id}' not found in the registry. Must be one of {', '.join(x['ID'].tolist())}.")

    dflow = x[x["ID"] == dataflow_id].iloc[0]["DataflowURL"]

    dataflow_json = httpx.get(dflow).json()
    dataflow_json_data = dataflow_json["data"]

    # Extracting concept schemes from the dataflow JSON
    concept_schemes = dataflow_json_data["conceptSchemes"]
    concept_schemes = extract_concept_schemes(concept_schemes)

    # Extracting data structures from the dataflow JSON
    data_structures = dataflow_json_data["dataStructures"]
    data_structures = extract_data_structures(data_structures)

    # Extracting metadata structures from the dataflow JSON
    metadata_structures = dataflow_json_data["metadataStructures"]
    metadata_structures = extract_metadata_structures(metadata_structures)

    dataflows = dataflow_json_data["dataflows"]
    dataflows = extract_dataflows(dataflows)

    glossaries = dataflow_json_data["glossaries"]
    glossaries = extract_glossary(glossaries)

    return {"ConceptSchemes": concept_schemes, "DataStructures": data_structures, "MetadataStructures": metadata_structures, "Dataflows": dataflows, "Glossaries": glossaries}


def datastructure(datastructure_id=None):

    x = dataflows_df()

    if datastructure_id not in x["ID"].values:
        raise ValueError(f"Data Structure ID '{datastructure_id}' not found in the registry. Must be one of {', '.join(x['ID'].tolist())}.")

    dstructure = x[x["ID"] == datastructure_id].iloc[0]["StructureURL"]

    # Fetching the data structure JSON from the IMF SDMX Plus API
    datastructure_json = httpx.get(dstructure).json()
    datastructure_json["data"].keys()

    concept_schemes = datastructure_json["data"]["conceptSchemes"]
    concept_schemes = extract_concept_schemes(concept_schemes)

    data_structures = datastructure_json["data"]["dataStructures"]
    data_structures = extract_data_structures(data_structures)

    metadata_structures = datastructure_json["data"]["metadataStructures"]
    metadata_structures = extract_metadata_structures(metadata_structures)

    glossary = datastructure_json["data"]["glossaries"]
    glossary = extract_glossary(glossary)

    return {"ConceptSchemes": concept_schemes, "DataStructures": data_structures, "MetadataStructures": metadata_structures, "Glossaries": glossary}


def testfunc(id):

    try:
        dataflow_info = dataflow(id)
        datastructure_info = datastructure(id)
        return dataflow_info, datastructure_info
    except ValueError as e:
        print(e)
