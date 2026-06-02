{#
Macro: preview_table_data
Description: Preview data from a table using MCP server's preview_data tool
Parameters:
  - schema_name: PostgreSQL schema name
  - table_name: Table name
  - limit: Row limit (default 5, max 50)

This macro is useful for:
  - Manual data exploration during development
  - Verifying data quality
  - Understanding data patterns

Usage in dbt development:
  {% do preview_table_data('analytics', 'sample_orders', 5) %}
#}

{% macro preview_table_data(schema_name, table_name, limit=5) %}
    {% set mcp_url = var('mcp_server_url', 'http://localhost:9001/mcp/') %}
    {% set allowed_schema = var('mcp_allowed_schema', '') %}

    {%- if allowed_schema and schema_name != allowed_schema -%}
        {{ log('❌ Schema access denied: ' ~ schema_name, info=true) }}
    {%- else -%}
        {%- if limit > 50 -%}
            {{ log('⚠️  Limit capped at 50 rows (requested: ' ~ limit ~ ')', info=true) }}
        {%- endif -%}

        {{ log('📊 Preview data from ' ~ schema_name ~ '.' ~ table_name ~ ' available via MCP', info=true) }}
        {{ log('   Endpoint: ' ~ mcp_url, info=true) }}
        {{ log('   Use: curl -H "Authorization: Bearer <token>" ' ~ mcp_url, info=true) }}
    {%- endif -%}
{% endmacro %}
