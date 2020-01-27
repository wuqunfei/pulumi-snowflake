from typing import Optional

from pulumi import Config, Input, Output, ResourceOptions
from pulumi.dynamic import Resource
from pulumi_snowflake.snowflake_connection_provider import \
    SnowflakeConnectionProvider

from .file_format_provider import FileFormatProvider


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

    database: Output[str]
    """
    The Snowflake database in which the file format exists.
    """

    schema: Output[str]
    """
    The Snowflake schema in which the file format exists.
    """

    def __init__(self,
                 resource_name: str,
                 database: Input[str],
                 type: Input[str],
                 name: Input[str] = None,
                 schema: Input[str] = None,
                 opts: Optional[ResourceOptions] = None):
        """
        :param str resource_name: The logical name of the resource.
        :param pulumi.Input[str] type: The name of the database in which to create the file format.
        :param pulumi.Input[str] type: The file format type.  One of `FileFormatType`.
        :param pulumi.Input[str] name: The physical Snowflake name of the file format.  Leave
                blank for autogenerated name.
        :param pulumi.Input[str] type: The name of the schema in which to create the file format.
        :param pulumi.ResourceOptions opts: Options for the resource.
        """

        config = Config()
        connection_provider = SnowflakeConnectionProvider(
            config.require('snowflakeUsername'),
            config.require('snowflakePassword'),
            config.require('snowflakeAccountName')
        )

        super().__init__(FileFormatProvider(connection_provider), resource_name, {
            'database': database,
            'resource_name': resource_name,
            'name': name,
            'type': type,
            'schema': schema
        }, opts)
        self.type = type
