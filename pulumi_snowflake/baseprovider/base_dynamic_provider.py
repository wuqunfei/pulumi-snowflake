from typing import List

from jinja2 import Environment
from pulumi.dynamic import ResourceProvider, CreateResult, DiffResult

from .filters import to_sql, to_identifier
from .. import Provider
from ..client import Client
from ..validation import Validation
from ..random_id import RandomId


class BaseDynamicProvider(ResourceProvider):
    """
    Generic base class for a Pulumi dynamic provider which manages Snowflake objects using a SQL
    connection.

    This class can be instantiated directly, but there are a couple of methods which can be overridden to account
    for slight differences in the way objects are created (e.g., whether they are scoped to a schema or
    to the account).  These methods are `get_full_object_name` and `generate_outputs`.
    """

    def __init__(self,
                 provider: Provider,
                 connection_provider: Client,
                 sql_name: str):
        self.provider_params = provider
        self.connection_provider = connection_provider
        self.sql_name = sql_name
        Validation.validate_object_type(sql_name)

    def create(self, inputs):

        # Validate inputs
        if inputs.get("name") is None and inputs.get("resource_name") is None:
            raise Exception("At least one of 'name' or 'resource_name' must be provided")

        validated_name = self._get_validated_autogenerated_name(inputs)

        # Perform SQL command to create object
        environment = self._create_jinja_environment()
        sql_statement = self._generate_sql_create_statement(validated_name, inputs, environment)
        self._execute_sql(sql_statement)

        # Generate provisional outputs from inputs.  Provisional because the call to generate_outputs below allows
        # subclasses to modify them if necessary.
        provisional_outputs = {
            "name": validated_name,
            **self._generate_outputs_from_inputs(inputs)
        }
        
        return CreateResult(
            id_=validated_name,
            outs=self._generate_outputs(validated_name, inputs, provisional_outputs)
        )

    def diff(self, id, olds, news):
        """
        Simple implementation which forces a replacement if any fields have changed.
        """
        ignoreFields = ["name", "resource_name", "__provider"]
        oldFields = set(filter(lambda k: k not in ignoreFields, olds.keys()))
        newFields = set(filter(lambda k: k not in ignoreFields, news.keys()))
        fields = list(oldFields.union(newFields))

        changed_fields = []

        for field in fields:
            if olds.get(field) != news.get(field):
                changed_fields.append(field)

        if (news.get("name") is not None and olds.get("name") != news.get("name")):
            changed_fields.append("name")

        return DiffResult(
            changes=len(changed_fields) > 0,
            replaces=changed_fields,
            delete_before_replace=True
        )

    def delete(self, id, props):
        validated_name = Validation.validate_identifier(id)
        full_name = self._get_full_object_name(props, validated_name)
        self._execute_sql(f"DROP {self.sql_name} {full_name}")

    def _get_validated_autogenerated_name(self, inputs):
        """
        If an object name is not provided, autogenerates one from the resource name, and validates the name.
        """
        name = inputs.get("name")

        if name is None:
            name = f'{inputs["resource_name"]}_{RandomId.generate(7)}'

        return Validation.validate_identifier(name)


    def _get_full_object_name(self, inputs, name):
        """
        Returns the full object name which is used in statements such as CREATE and DELETE
        """

        Validation.validate_identifier(name)

        # A fully qualified name is only used if the db and schema are explicit in the inputs.  If they are only
        # present in the providers, then we can assume either this resource is not scoped to a schame or Snowflake is
        # handling it
        if inputs.get("database") or inputs.get("schema"):
            (database, schema) = self._get_database_and_schema(inputs)

            Validation.validate_identifier(database)
            Validation.validate_identifier(schema)

            if database is not None and schema is not None:
                return f"{database}.{schema}.{name}"
            elif database is not None and schema is None:
                return f"{database}..{name}"
            else:
                return name
        else:
            return name

    def _generate_outputs(self, name, inputs, outs):
        """
        Appends the schema, database and fully-qualified object name to the outputs.
        """

        (database, schema) = self._get_database_and_schema(inputs)

        if database is not None:
            return {
                "database": database,
                "schema": schema,
                "full_name": self._get_full_object_name(inputs, name),
                **outs
            }
        else:
            return {
                "full_name": name,
                **outs
            }

    def _get_database_and_schema(self, inputs):
        database = None
        schema = None

        if inputs.get("database") or inputs.get("schema"):

            if self.provider_params is not None:
                database = self.provider_params.database if self.provider_params.database else None
                schema = self.provider_params.schema if self.provider_params.schema else None

            database = inputs.get("database") if inputs.get("database") else database
            schema = inputs.get("schema") if inputs.get("schema") else schema

        return (database, schema)

    def _generate_outputs_from_inputs(self, inputs):
        """
        Creates an outputs dictionary which has the values provided in the inputs, with the exception of
        `name` and `resource_name`  - these are handled separately to allow for autogeneration of names
        """
        keys = filter(lambda k: k != 'resource_name' and k != 'name', inputs.keys())
        outputs = {k: inputs.get(k) for k in keys}
        return outputs

    def _generate_sql_create_statement(self, validated_name, inputs, environment=None):
        raise Exception("The BaseDynamicProvider class cannot be used directly, please create a subclass and "
                        "implement _generate_sql_create_statement")

    def _execute_sql(self, statement):
        connection = self.connection_provider.get()
        cursor = connection.cursor()

        try:
            cursor.execute(statement)
        finally:
            cursor.close()

        connection.close()

    def _create_jinja_environment(self):
        """
        Convenience method which creates a Jinja environment with additional filters for SQL generation.
        """
        environment = Environment()
        environment.filters["sql"] = to_sql
        environment.filters["sql_identifier"] = to_identifier
        return environment