-- Setup script for the Hello Snowflake! app.

CREATE APPLICATION ROLE IF NOT EXISTS app_public;
CREATE SCHEMA IF NOT EXISTS core;
GRANT USAGE ON SCHEMA core TO APPLICATION ROLE app_public;

-- ✅ External Network Access Configuration (PERMISSIONS SEULEMENT)
-- 1. Règle réseau pour autoriser l'accès à l'API LangGraph
CREATE OR REPLACE NETWORK RULE langgraph_api_network_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('ht-nautical-decoration-70-7d3b580d2cc25c4fb59221f2145e155e.us.langgraph.app');

-- 2. Secret pour l'API key LangGraph  
CREATE OR REPLACE SECRET langgraph_api_secret
  TYPE = GENERIC_STRING
<<<<<<< HEAD
  SECRET_STRING = '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';
=======
  SECRET_STRING = '***REMOVED***';
>>>>>>> 721f07df31ba0d8b19d36c039cc971619d0ea222

-- 3. Intégration d'accès externe
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION langgraph_external_access_integration
  ALLOWED_NETWORK_RULES = (langgraph_api_network_rule)
  ALLOWED_AUTHENTICATION_SECRETS = (langgraph_api_secret)
  ENABLED = TRUE;

-- Permissions pour l'application
GRANT USAGE ON INTEGRATION langgraph_external_access_integration TO APPLICATION ROLE app_public;
GRANT READ ON SECRET langgraph_api_secret TO APPLICATION ROLE app_public;

-- Hello world example (inchangé)
CREATE OR REPLACE PROCEDURE CORE.HELLO()
  RETURNS STRING
  LANGUAGE SQL
  EXECUTE AS OWNER
  AS
  BEGIN
    RETURN 'Hello Snowflake!';
  END;

GRANT USAGE ON PROCEDURE core.hello() TO APPLICATION ROLE app_public;

-- Streamlit app (inchangé)
CREATE OR ALTER VERSIONED SCHEMA code_schema;
GRANT USAGE ON SCHEMA code_schema TO APPLICATION ROLE app_public;

CREATE STREAMLIT IF NOT EXISTS code_schema.hello_snowflake_streamlit
  FROM '/streamlit'
  MAIN_FILE = '/client.py';     

GRANT USAGE ON STREAMLIT code_schema.hello_snowflake_streamlit TO APPLICATION ROLE app_public;