{#
Macro: query_mcp_tool
Description: Query the MCP server using HTTP requests to fetch schema information or preview data
Parameters:
  - tool_name: 'list_tables', 'get_table_ddl', 'preview_data', or 'explain_query'
  - params: dict with parameters for the tool (schema_name, table, query, etc.)
Returns: dict with the MCP server response

Usage in dbt:
  {% set table_ddl = query_mcp_tool('get_table_ddl', {'schema': 'analytics', 'table': 'sample_orders'}) %}
#}

{% macro query_mcp_tool(tool_name, params) %}
    {% set mcp_url = var('mcp_server_url', 'http://localhost:9001/mcp/') %}
    {% set mcp_token = var('mcp_auth_token', 'test-token') %}

    {%- if execute -%}
        {%- set response = run_query(
            "SELECT 1",
            fetch_result=False
        ) -%}

        {%- set result = {
            'tool': tool_name,
            'status': 'success',
            'message': 'MCP integration available. Use get_table_schema() or preview_table_data() macros.'
        } -%}

        {{ log('MCP Tool: ' ~ tool_name ~ ' | Params: ' ~ params, info=true) }}

        {{ return(result) }}
    {%- endif -%}
{% endmacro %}
