# Data flows

## Input

NSPS accepts **webhook events** from PortaBilling ESPF via secure HTTP. The events contain minimal information:

<details>
  <summary>Example of ESPF event</summary>

```json title="Example of ESPF event" linenums="1"
{
    "event_type": "SIM/Updated",
    "variables": {
        "i_env": 3,
        "i_event": 999999,
        "i_account": 277147,
        "event_time": "2025-05-01 12:00:00"
    }
}
```

</details>

Key input fields:

- `event_type`: Identifies the type of event (e.g., "Account/Unblocked", "SIM/Updated").
- `variables`: Contains identifiers and metadata for the event.
- `i_event`: Unique event identifier in PortaBilling.
- `i_account`: Account identifier affected by the event.
- `event_time`: Optional timestamp when the event occurred (format: "YYYY-MM-DD HH:MM:SS" in UTC).

The set of fields in the variables object may vary depending on the event type (`event_type`). Authentication is performed via HTTP Basic Auth with configurable credentials.

## Output

NSPS outputs enriched events to **connector microservices**, which are responsible for interfacing with external systems. The enriched event contains all necessary data for provisioning:

<details>
  <summary>Example of enriched event</summary>

```json title="Example of enriched event" linenums="1"
{
    "event_id":"3e84c79f-ab6f-4546-8e27-0b6ab866f1fb",
    "data":{
        "event_type":"SIM/Updated",
        "variables":{
            "i_env":1,
            "i_event":999999,
            "i_account":1,
            "curr_status":"used",
            "prev_status":"active"
        }
    },
    "pb_data":{
        "account_info":{
            "bill_status":"open",
            "billing_model":"credit_account",
            "blocked":false,
            "i_account":1,
            "i_customer":6392,
            "i_product":3774,
            "id":"79123456789@msisdn",
            "phone1":"",
            "product_name":"wtl Pay as you go",
            "time_zone_name":"Europe/Prague",
            "assigned_addons":[
                {
                    "addon_effective_from":"2025-05-16T12:59:46",
                    "addon_priority":10,
                    "description":"",
                    "i_product":3775,
                    "i_vd_plan":1591,
                    "name":"wtl Youtube UHD"
                }
            ],
            "service_features":[
                {
                    "name":"netaccess_policy",
                    "effective_flag_value":"Y",
                    "attributes":[
                        {
                            "name":"access_policy",
                            "effective_value":"179"
                        }
                    ]
                }
            ]
        },
        "sim_info":{
            "i_sim_card":3793,
            "imsi":"001010000020349",
            "msisdn":"79123456789",
            "status":"active"
        },
        "access_policy_info":{
            "i_access_policy":179,
            "name":"WTL integration test",
            "attributes":[
                {
                    "group_name":"lte.wtl",
                    "name":"cs_profile",
                    "value":"cs-pp-20250319"
                },
                {
                    "group_name":"lte.wtl",
                    "name":"eps_profile",
                    "value":"eps-pp-20250319"
                }
            ]
        },
        "product_info":{
            "name":"DEV WTL Pay as you go",
            "description":"",
            "addon_priority":0,
            "i_product":658
        },
        "full_vd_counter_info":[
            {
                "service_name":"Internet Access KB",
                "vdp_name":"DEV WTL Free 10MB (1 day)",
                "i_vd_plan":204,
                "i_dest_group":2650,
                "addon_priority":10,
                "i_vd_dg":283,
                "remaining":"10",
                "i_service":106,
                "dg_name":"RG100",
                "discount_info":"0..10 - 100%",
                "unit":"megabyte",
                "allocated_amount":10
            }
        ]
    },
    "handler_id":"wtl-hlr-hss-nsps",
    "created_at":"2025-03-12T16:47:30.443939+00:00",
    "updated_at":"2025-03-12T16:47:36.585885+00:00",
    "status":"received"
}

```

</details>

The connectors, which are outside the NSPS black box, then transform this enriched data into formats specific to each external system. Depending on the event type and the target external system, different subsets of these fields may be used for the transformation.