from pulumi import ResourceOptions, Input, Output, Config
from pulumi.dynamic import Resource
from typing import Optional
from .FileFormatProvider import FileFormatProvider


class FileFormatType:
    CSV = "CSV"
    JSON = "JSON"
    AVRO = "AVRO"
    ORC = "ORC"
    PARQUET = "PARQUET"
    XML = "XML"


class FileFormat(Resource):
    """
    Represents a Snowflake File Format.  See
    https://docs.snowflake.net/manuals/sql-reference/sql/create-file-format.html
    for more details of parameters.
    """

    name: Output[str]
    """
    The name of the file format in Snowflake.
    """

    type: Output[str]
    """
    The file format type.  One of `FileFormatType`.
    """

    def __init__(self,
                 resource_name: str,
                 type: Input[str],
                 name: Input[str] = None,
                 opts: Optional[ResourceOptions] = None):
        """
        :param str resource_name: The logical name of the resource.
        :param pulumi.Input[str] type: The file format type.  One of `FileFormatType`.
        :param pulumi.Input[str] name: The physical Snowflake name of the file format.  Leave
                blank for autogenerated name.
        :param pulumi.ResourceOptions opts: Options for the resource.
        """

        config = Config()
        super().__init__(FileFormatProvider(), resource_name, {
            'name': name,
            'type': type,
            'snowflakeAccountName': config.require_secret('snowflakeAccountName'),
            'snowflakeUsername': config.require_secret('snowflakeUsername'),
            'snowflakePassword': config.require_secret('snowflakePassword'),
        }, opts)
        self.type = type
