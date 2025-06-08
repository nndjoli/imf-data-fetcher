from .utils import *
from .queries import *
from typing import Optional, List


class IMFInstance:
    """
    Instance of the IMF Data API.
    This class provides methods to access dataflows and their associated structures.
    It allows querying dataflows by their ID and retrieving information about dimensions and available values.
    Usage:
    >>> imf_instance = IMFInstance()
    >>> dataflow = imf_instance.Dataflow('CPI')
    >>> dataflow.dataflow_name  # Returns the name of the dataflow
    >>> dataflow.dimensions  # Returns a DataFrame of dimensions in the dataflow
    >>> dataflow.query_params_dict_template  # Returns a template for query parameters
    >>> query_params = {'DIM1': 'USA', 'DIM2': '*'}
    >>> result = dataflow.query(query_params)  # Queries the dataflow with specified parameters
    >>> print(result)  # Prints the queried data as a DataFrame/ a dictionary of DataFrames

    """

    def __init__(self):

        self.dataflows: pd.DataFrame = get_all_dataflows()
        """
        DataFrame containing all dataflows available in the IMF Data API.
        Each row corresponds to a dataflow with its properties such as ID, name, version, and agency ID.
        """

        self.dataflows_ids: list[str] = self.dataflows["DataflowID"].tolist()
        """
        List of dataflow IDs available in the IMF Data API.
        This is used to quickly check if a dataflow with a given ID exists.
        """

    def dataflow_dictionary(self, dataflow_id: str) -> dict:
        """
        Returns a dictionary of the dataflow with the given ID.
        """
        ids = self.dataflows_ids
        dicts = self.dataflows.to_dict(orient="records")

        if dataflow_id not in ids:
            raise ValueError(f"Dataflow ID '{dataflow_id}' not found. Available IDs: {ids}")

        for dictionary in dicts:
            if dictionary["DataflowID"] == dataflow_id:
                return dictionary

        raise ValueError(f"Dataflow ID '{dataflow_id}' not found in dataflow dictionaries.")

    def Dataflow(self, dataflow_id: str) -> "IMFInstance.DataflowObject":
        """
        Returns an instance of the DataflowObject for the specified dataflow ID.
        This object provides methods to query the dataflow and access its dimensions and available values.

         Parameters:
        dataflow_id (str): The ID of the dataflow to be accessed.

        """
        return IMFInstance.DataflowObject(self, dataflow_id)

    class DataflowObject:

        instance: Optional["IMFInstance"]

        dataflow_id: str
        dataflow_dictionary: Optional[dict]
        dataflow_name: Optional[str]
        dataflow_version: Optional[str]
        dataflow_agency_id: Optional[str]

        structure_id: Optional[str]
        structure_version: Optional[str]
        structure_agency_id: Optional[str]

        queries_response: Optional[dict]

        dimensions: Optional[pd.DataFrame]
        dimensions_codelists: Optional[dict]
        dimensions_available_values: Optional[pd.DataFrame]
        _dimensions_available_values: Optional[dict]
        dimensions_ordered: Optional[List[str]]

        query_params_dict_template: Optional[dict]

        def __init__(self, parent: "IMFInstance", dataflow_id: str):

            self.instance = parent

            self.dataflow_id = dataflow_id

            """
            ID of the dataflow.
            """

            self.dataflow_dictionary = parent.dataflow_dictionary(dataflow_id)
            """
            Dictionary containing the dataflow information.
            """

            self.dataflow_name = self.dataflow_dictionary.get("DataflowName")
            """
            Name of the dataflow.
            """

            self.dataflow_version = self.dataflow_dictionary.get("DataflowVersion")
            """
            Version of the dataflow. Always corresponds to the latest version.
            """

            self.dataflow_agency_id = self.dataflow_dictionary.get("DataflowAgencyID")
            """
            Agency ID of the dataflow.
            """

            self.structure_id = self.dataflow_dictionary.get("StructureID")
            """
            ID of the datastructure associated with the dataflow.
            """

            self.structure_version = self.dataflow_dictionary.get("StructureVersion")
            """
            Version of the datastructure associated with the dataflow. Always corresponds to the latest version.
            """

            self.structure_agency_id = self.dataflow_dictionary.get("StructureAgencyID")
            """
            Agency ID of the datastructure associated with the dataflow.
            """

            self.queries_response = asyncio.run(queries(self.dataflow_dictionary))

            self.dimensions = process_dataflow_dimensions(self.queries_response)
            """
            DataFrame containing the dimensions (query parameters) of the dataflow.
            Each row corresponds to a dimension with its properties.
            """

            self.dimensions_codelists = process_codelists(self.queries_response, self.dimensions)
            """
            Dictionary containing the codelists for each dimension.
            The keys are dimension concept IDs, and the values are lists of dictionaries with "ID" and "Name".
            """

            self.dimensions_available_values, self._dimensions_available_values = process_availability(self.queries_response, self.dimensions_codelists)
            """
            DataFrame containing the available values for each dimension in the dataflow.
            Each row corresponds to a dimension value with its properties.
            The DataFrame has columns "DimensionID", "Value", and "Name".
            "_dimensions_available_values" is a dictionary mapping dimension names to their available values.
            """

            self.dimensions_ordered = self.dimensions.sort_values(by="ConceptPosition")["ConceptName"].to_list()
            """
            List of dimension names in the order they appear in the dataflow.
            This is used to ensure that query parameters are provided in the correct order when querying the dataflow.
            """

            self.query_params_dict_template = {dimension: "*" for dimension in self.dimensions_ordered}
            """
            Dictionary template for query parameters.
            The keys are dimension names, and the values are "Value", indicating that these are the expected parameters for querying the dataflow.
            """

        def dimension_codelist(self, dimension_concept_id: Optional[str] = None):
            """
            Returns a dictionary of codelist for specified dimension.
            """
            if self.dimensions_codelists is None:
                raise ValueError("No codelists available for this dataflow.")
            try:
                return self.dimensions_codelists[dimension_concept_id]
            except KeyError:
                raise ValueError(f"Dimension ID '{dimension_concept_id}' not found. Available IDs: {list(self.dimensions_codelists.keys())}")

        def dimension_available_values(self, dimension_concept_name: Optional[str] = None):
            """
            Returns a dictionary of available values for specified dimension.
            """
            if self._dimensions_available_values is None:
                raise ValueError("No available values for dimensions. The dataflow may not be initialized properly.")
            try:
                if dimension_concept_name is None:
                    raise ValueError("dimension_concept_name cannot be None.")
                dimension_concept_name = dimension_concept_name.upper()
                return self._dimensions_available_values[dimension_concept_name]
            except KeyError:
                raise ValueError(f"Dimension ID '{dimension_concept_name}' not found. Available IDs: {list(self._dimensions_available_values.keys())}")

        def query(self, query_params: dict) -> pd.DataFrame:
            """
            Queries the dataflow with the provided query parameters.
            The query parameters must match the template defined in `query_params_dict_template`.
            The keys of the query parameters must match the dimension names in the dataflow.
            The values can be a single value or a list of values for each dimension.
            If a value is not provided for a dimension, it defaults to "*", which means all values for that dimension.
            The method returns a DataFrame or a dict of DataFrames containing the queried data if the query is successful.
            If the query fails, it raises an exception with a descriptive error message.
            """

            if not isinstance(query_params, dict):
                raise TypeError(f"Query parameters must be a dict matching {list(self.query_params_dict_template.keys())}")

            if self.query_params_dict_template is None:
                raise ValueError("Query parameter template is not initialized. Please check the dataflow initialization.")
            template_keys = list(self.query_params_dict_template.keys())
            provided_keys = list(query_params.keys())
            if set(provided_keys) != set(template_keys):
                missing = set(template_keys) - set(provided_keys)
                extra = set(provided_keys) - set(template_keys)
                msgs = []
                if missing:
                    msgs.append(f"missing {missing}")
                if extra:
                    msgs.append(f"unexpected {extra}")
                raise ValueError(f"Expected keys {template_keys}, but got {provided_keys} ({'; '.join(msgs)})")

            formatted = []
            for key in template_keys:
                val = query_params.get(key, "*")
                if val is None or val == "*":
                    formatted.append("*")
                elif isinstance(val, list):
                    formatted.append("+".join(str(v).upper() for v in val))
                else:
                    formatted.append(str(val).upper())

            if self.dimensions_available_values is None:
                raise ValueError("No available values for dimensions. The dataflow may not be initialized properly.")

            available = self.dimensions_available_values.groupby("DimensionID")["Value"].apply(list).to_dict()

            value_names = []
            for dim_key, token in zip(template_keys, formatted):
                if token == "*":
                    continue
                for part in token.split("+"):
                    if part not in available.get(dim_key, []):
                        raise ValueError(f"Value '{part}' for dimension '{dim_key}' not in available values")
                    value_row = self.dimensions_available_values.loc[self.dimensions_available_values["Value"] == part, "Name"]
                    value_name = value_row.values[0] if not value_row.empty else str(part)  # type: ignore
                    if value_name is None:
                        value_name = str(part)
                    value_names.append(value_name)

            key = ".".join(formatted)
            key_name = ", ".join(value_names)
            print(f"Querying: {key_name}")
            data = process_queried_data(query_data(self.dataflow_agency_id, self.dataflow_id, key))

            if len(data.keys()) == 1:
                data = data[list(data.keys())[0]]
                data.name = key_name
                return data

            return data  # type: ignore
