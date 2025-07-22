#bin/bash
SNOWFLAKE_PASSWORD='y5Y1PdyU25V%!2!'

snow connection add \
  --connection-name dev-connection2 \
  --account XDPMUYX-LF54199 \
  --user DEV \
  --password $SNOWFLAKE_PASSWORD \
  --role DEV \
  --warehouse COMPUTE_DEV \
  --database SANDBOX \
  --schema SANDBOX_SCHEMA \
  --host xdpmuyx-lf54199.snowflakecomputing.com \
  --port 443 \
  --region westeurope \
  --authenticator snowflake \
  --no-interactive \
  --format json \
  --verbose
