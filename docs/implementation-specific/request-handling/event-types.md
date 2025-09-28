# Event Types

## SIM/Updated

### Trigger conditions

- SIM card details have been changed, e.g., the default PIN for inactive SIM cards has been changed.
- The SIM card data specified in a custom field has been changed, e.g., the “Amazon” value is set in the “Marketplace” custom field.
- [SIM card status][sim-card-status] has been changed, e.g., from “In use” to “Disposed”.
- An account’s ID has changed. ([Account.id][account.id] has been updated.)
- Another product was assigned to the account. An account’s product has changed. (Account.i_product has been updated.)
- An account’s add-on product has been changed.
- An add-on product has been removed from an account.
- A new add-on product has been added for an account.
- The user has topped up (“recharged”) their bundle of any service type to get more service volume before bundle renewal.
- An account has exceeded its service usage quota (for services of all types except **Messaging** and **Internet access**).
- A service feature has been enabled/disabled for an account (the Service_Attribute_Values table has been updated).
- Custom information (e.g., ID card) has been added or changed for an account. (The Custom_Field_Values table has been updated for the account.)
- An account’s billing status has been changed or affected by the customer’s billing status. A customer’s status has changed. (Customers.bill_status has changed.)
- An account has been blocked. (Accounts.blocked set to ‘Y.’)
- An account has been unblocked. (Accounts.blocked set to ‘N.’)
- Bundle is successfully activated for the first time (the bundle has never been activated for this account before).
- Bundle is assigned to the account.
- Bundle has expired (for bundles of the [balance-dependant renewable type][bundles]).
- Grace period for the bundle is over (for [balance-dependant renewable type][bundles]).
- Bundle is removed from the account.
- Bundle is automatically renewed for the account (for bundles of the [balance-dependant renewable type][bundles]).
- Bundle is successfully activated after expiration (for bundles of the [balance-dependant renewable type][bundles]).

### Most used fields

- `pb_data.sim_info.imsi`
- `pb_data.account_info.i_account`
- `pb_data.account_info.i_product`
- `pb_data.account_info.bill_status`
- `pb_data.account_info.blocked`
- `pb_data.account_info.product_name`
- `pb_data.account_info.assigned_addons[].i_product`
- `pb_data.account_info.assigned_addons[].name`
- `pb_data.account_info.assigned_addons[].i_vd_plan`
- `pb_data.access_policy_info.attributes["name"=="cs_profile"].values[0]`
- `pb_data.access_policy_info.attributes["name"=="eps_profile"].values[0]`

## SIM/Created

### Trigger conditions

- A SIM card has been added to the inventory.

### Most used fields

- `pb_data.sim_info.imsi`
- `pb_data.account_info.i_account`

## SIM/Deleted

### Trigger conditions

- A SIM card has been removed from the inventory.

### Most used fields

- `pb_data.sim_info.imsi`
- `pb_data.account_info.i_account`

## SIM/Replaced

### Trigger conditions

- A SIM card has been assigned to, removed from, or changed for an account.

### Most used fields

- `pb_data.sim_info`
- `pb_data.prev_sim_info`

<!-- References -->

[sim-card-status]: https://docs.portaone.com/docs/mr122-sim-card-inventory?topic=comprehensive-details-and-group-operations-in-sim-card-inventory
[account.id]: http://Account.id
[bundles]: https://docs.portaone.com/docs/mr122-balance-dependent-renewable-bundles
