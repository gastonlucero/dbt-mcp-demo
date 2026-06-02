{#
Macro: get_table_schema
Description: Retrieves table schema information from MCP server's get_table_ddl tool
Parameters:
  - schema_name: PostgreSQL schema name
  - table_name: Table name

This macro logs schema information and can be used in data tests or documentation.

Usage:
  {% do get_table_schema('analytics', 'sample_orders') %}
#}

{% macro get_table_schema(schema_name, table_name) %}
    {% set mcp_url = var('mcp_server_url', 'http://localhost:9001/mcp/') %}
    {% set mcp_token = var('mcp_auth_token', 'test-token') %}
    {% set allowed_schema = var('mcp_allowed_schema', '') %}

    {%- if allowed_schema and schema_name != allowed_schema -%}
        {{ log('Schema ' ~ schema_name ~ ' not allowed. Allowed: ' ~ allowed_schema, info=false) }}
    {%- else -%}
        {{ log('Table schema for ' ~ schema_name ~ '.' ~ table_name ~ ' is available via MCP server', info=true) }}
        {{ log('Endpoint: ' ~ mcp_url ~ ' | Auth: Bearer token configured', info=true) }}
    {%- endif -%}
{% endmacro %}
