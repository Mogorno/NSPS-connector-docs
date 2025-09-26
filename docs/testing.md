# Testing

First, you can make sure that the service is up and running by sending a **health check request**.

<details>
<summary>Example</summary>

```bash
$ curl https://[TAG---]SERVICE_NAME-PROJECT_NUMBER.REGION.run.app
```

```json
{
    "status": "Healthy"
}
```

</details>

Then you need to send a request with the expected data structure

<details>
<summary>Example</summary>

```bash
curl -X POST https://[TAG---]SERVICE_NAME-PROJECT_NUMBER.REGION.run.app \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "3e84c79f-ab6f-4546-8e27-0b6ab866f1fb",
    "data": {
      "event_type": "SIM/Updated",
      "variables": {
        "i_env": 1,
        "i_event": 999999,
        "i_account": 1,
        "curr_status": "used",
        "prev_status": "active"
      }
    },
    "pb_data": {
      "account_info": {
        "bill_status": "open",
        "billing_model": "credit_account",
        "blocked": false,
        "firstname": "Serhii",
        "i_account": 1,
        "i_customer": 6392,
        "i_product": 3774,
        "id": "79123456789@msisdn",
        "lastname": "Dolhopolov",
        "phone1": "",
        "product_name": "Pay as you go",
        "time_zone_name": "Europe/Prague",
        "assigned_addons": [
          {
            "addon_effective_from": "2025-05-16T12:59:46",
            "addon_priority": 10,
            "description": "",
            "i_product": 3775,
            "i_vd_plan": 1591,
            "name": "Youtube UHD"
          }
        ],
        "service_features": [
          {
            "name": "netaccess_policy",
            "effective_flag_value": "Y",
            "attributes": [
              {
                "name": "access_policy",
                "effective_value": "179"
              }
            ]
          }
        ]
      },
      "sim_info": {
        "i_sim_card": 3793,
        "imsi": "001010000020349",
        "msisdn": "79123456789",
        "status": "active"
      },
      "access_policy_info": {
        "i_access_policy": 179,
        "name": "Integration test",
        "attributes": [
          {
            "group_name": "lte.wtl",
            "name": "cs_profile",
            "value": "cs-pp-20250319"
          },
          {
            "group_name": "lte.wtl",
            "name": "eps_profile",
            "value": "eps-pp-20250319"
          }
        ]
      }
    },
    "handler_id": "hlr-hss-nsps",
    "created_at": "2025-03-12T16:47:30.443939+00:00",
    "updated_at": "2025-03-12T16:47:36.585885+00:00",
    "status": "received"
  }'
```

```json
{ "message": "Event processed successfully" }
```

</details>

**What should be tested:**

- Authentication.
- Response codes (2XX, 4XX, 5XX).
- Changes to the external system.

It is worth testing this service with some kind of external staging system. It is not recommended to use production immediately without being sure that the service works correctly.