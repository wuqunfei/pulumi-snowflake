from .. import Client
from ..baseprovider import BaseDynamicProvider
from ..provider import Provider
from ..validation import Validation


class SchemaProvider(BaseDynamicProvider):
    """
    Dynamic provider for Snowflake Schema resources.
    """

    def __init__(self, provider_params: Provider, connection_provider: Client):
        super().__init__(provider_params, connection_provider)

    def generate_sql_create_statement(self, validated_name, inputs, environment):
        template = environment.from_string(
"""CREATE{% if transient %} TRANSIENT{% endif %} SCHEMA {{ full_name }}
{% if data_retention_time_in_days %}DATA_RETENTION_TIME_IN_DAYS = {{ data_retention_time_in_days | sql }}
{% endif %}
{%- if comment %}COMMENT = {{ comment | sql }}
{% endif %}
""")

        sql = template.render({
            "full_name": self._get_full_object_name(inputs, validated_name),
            **inputs
        })

        return sql

    def generate_sql_drop_statement(self, validated_name, inputs, environment):
        template = environment.from_string("DROP SCHEMA {{ full_name }}")
        sql = template.render({
            "full_name": self._get_full_object_name(inputs, validated_name)
        })
        return sql

    def _get_full_object_name(self, inputs, name):
        """
        Schemas are unique since they are the only object scoped to databases.  Their fully-qualified
        name format is therefore different.
        """
        Validation.validate_identifier(name)

        if inputs.get("database"):
            database = inputs["database"]
            Validation.validate_identifier(database)
            return f"{database}.{name}"
        else:
            return name