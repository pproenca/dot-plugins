#!/usr/bin/env bash
# Stages a mapped object type plus its source DDL, ready for stage 04.
set -euo pipefail
mkdir -p ontology/object-types ontology/mappings
cat > ontology/object-types/customer.yaml <<'YAML'
apiName: customer
displayName: Customer
pluralDisplayName: Customers
description: An organisation that buys from us.
primaryKey: customerId
titleProperty: customerName
properties:
  customerId:
    type: string
    description: Stable identifier issued by the CRM when the account is opened.
    required: true
  customerName:
    type: string
    description: Registered trading name of the customer.
    required: true
  signupDate:
    type: date
    description: Date the account was opened.
    required: true
  creditRating:
    type: string
    description: Risk grade set by a credit analyst. Populated by the SetCreditRating action.
YAML
cat > ontology/mappings/customer.yaml <<'YAML'
objectType: customer
sources:
  - name: CRM.RAW.CUSTOMER_V2
    system: snowflake
    grain: One row per customer_id. No history.
    freshness: Batch, lands daily by 06:00 UTC.
propertyMappings:
  customerId:
    column: CUSTOMER_ID
    columnType: VARCHAR(36)
  customerName:
    column: CUST_NM
    columnType: VARCHAR(255)
    transformation: Trim trailing whitespace.
  signupDate:
    column: SIGNUP_DT
    columnType: DATE
unmapped:
  creditRating: Populated by the SetCreditRating action. No source column.
excluded:
  - column: ETL_LOAD_TS
    reason: Pipeline metadata.
  - column: _ROW_HASH
    reason: Internal change-detection hash.
YAML
