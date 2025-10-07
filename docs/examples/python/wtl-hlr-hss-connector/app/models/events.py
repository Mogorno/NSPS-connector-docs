from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum, IntEnum


class EventType(str, Enum):
    """Supported event types"""
    SIM_UPDATED = "SIM/Updated"


class BillStatus(str, Enum):
    """Bill status enum"""
    OPEN = "open"
    INACTIVE = "inactive"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


class ServiceFeatureAttribute(BaseModel):
    """Service feature attribute model"""
    name: Optional[str] = Field(
        None,
        description="The service feature attribute internal name",
        examples=["access_policy"]
    )
    effective_value: Optional[str] = Field(
        None,
        description="Service feature attribute value, comma-separated if multiple values",
        examples=["149"]
    )


class ServiceFeature(BaseModel):
    """Service feature model"""
    name: Optional[str] = Field(
        None, 
        description="The service feature name",
        examples=["netaccess_policy"]
    )
    effective_flag_value: Optional[str] = Field(
        None, 
        description="The actual service feature flag value",
        examples=["Y"]
    )
    attributes: List[ServiceFeatureAttribute] = Field(
        default_factory=list, 
        description="The list of service feature attributes"
    )


class AddOnProduct(BaseModel):
    """Addon product model"""
    addon_effective_from: Optional[str] = Field(
        None, 
        description="ISO datetime string - when the add-on product is activated",
        examples=["2025-05-16 12:59:46"]
    )
    addon_effective_to: Optional[str] = Field(
        None, 
        description="ISO datetime string - when the add-on product expires",
        examples=["2025-06-16 12:59:46"]
    )
    addon_priority: Optional[int] = Field(
        None,
        description="Priority of the addon: 0=main product, 10=low, 15=medium low, 20=medium, 25=medium high, 30=high",
        examples=[10]
    )
    description: Optional[str] = Field(
        None, 
        description="The internal product description",
        examples=[None]
    )
    i_product: Optional[int] = Field(
        None, 
        title="Product ID",
        description="The unique ID of the product",
        examples=[3775]
    )
    i_product_group: Optional[int] = Field(
        None,
        title="Product Group ID",
        description="The unique ID of the product group to which the product belongs",
        examples=[None]
    )
    i_vd_plan: Optional[int] = Field(
        None,
        title="VolumeDiscount Plan ID",
        description="The unique ID of the bundle assigned to the product",
        examples=[1591]
    )
    name: Optional[str] = Field(
        None,
        description="The product name",
        examples=["Youtube UHD"]
    )


class AccountInfo(BaseModel):
    """Account information model"""
    bill_status: Optional[str] = Field(
        None,
        title="Billing status",
        description=(
            "The billing status of the account.<br> "
            'Possible values: "open" - the account is open;<br> '
            '"suspended" - the account is suspended. This status is available for debit accounts and can be set only automatically (by subscriptions assigned to the account);<br> '
            '"inactive" - the account is inactive. This status can be set only during account creation, manually or using the Account Generator;<br> '
            '"terminated" - the account is terminated. This status can be set only via the terminate_account method.'
        ),
        examples=["open"]
    )
    billing_model: Optional[str] = Field(
        None,
        title="Account type",
        description=(
            "The account type.<br> "
            "An account can be a debit, credit, beneficiary, or voucher type.<br> "
            "A debit type is usually associated with prepaid cards and the account balance will show the available funds.<br> "
            "A credit account is invoiced for incurred costs.<br> "
            "A beneficiary account has a service configuration that only uses the balance, products, and quotas of a sponsor account.<br> "
            "A voucher-type account is used to refill debit or credit accounts; the balance of the voucher account is transferred to the main account.<br> "
            'Possible values: "debit_account", "recharge_voucher", "credit_account", "alias", "beneficiary".'
        ),  
        examples=["credit_account"]
    )
    blocked: Optional[bool] = Field(
        None,
        description=(
            "Indicates whether account's calls and "
            "access to the self-care interface is blocked"
        ),
        examples=[False]
    )
    email: Optional[str] = Field(
        None,
        description="The email address associated with the account",
        examples=["info@portaone.com"]
    )
    firstname: Optional[str] = Field(
        None,
        title="First name",
        description="The account owner's first name",
        examples=["John"]
    )
    i_account: Optional[int] = Field(
        None, 
        title="Account unique ID",
        description="The unique ID of the account",
        examples=[277147]
    )
    i_customer: Optional[int] = Field(
        None, 
        title="Customer ID",
        description="The ID of the customer record to which the account belongs",
        examples=[6392]
    )
    i_master_account: Optional[int] = Field(
        None,
        title="Master Account ID",
        description="The ID of the parent account", 
        examples=[None]
    )
    i_product: Optional[int] = Field(
        None, 
        title="Product ID",
        description="The ID for the account's product",
        examples=[3774]
    )
    i_vd_plan: Optional[int] = Field(
        None,
        title="VolumeDiscount Plan ID",
        description=(
            "The unique ID of the bundle assigned to the account individually"
        ),
        examples=[1591]
    )
    id: Optional[str] = Field(
        None,
        description="The unique ID (PIN) of the account on the interface",
        examples=["380661310764@msisdn"]
    )
    lastname: Optional[str] = Field(
        None,
        title="Last name",
        description="The account owner's last name",
        examples=["Doe"]
    )
    phone1: Optional[str] = Field(
        None, 
        description="The main phone number",
        examples=["380661310764"]
    )
    product_name: Optional[str] = Field(
        None,
        description="The name of the account's product",
        examples=["Pay as you go"]
    )
    status: Optional[str] = Field(
        None,
        description=(
            "The current status of the account, based on its own status, the customer's status and other factors (like 'expiration time', 'activation time' and so on).<br> "
            'Possible values:<br>'
            '"active" - the account is active;<br>'
            '"customer_exported" - the account\'s customer is exported;<br>'
            '"expired" - the account expired;<br>'
            '"quarantine" - after being screened, the account was unable to supply valid credentials;<br>'
            '"screening" - the suspicious activity was detected for the account;<br>'
            '"closed" - the account is closed;<br>'
            '"inactive" - the account is inactive;<br>'
            '"suspended" - the account is suspended (applicable to debit accounts only);<br>'
            '"customer_suspended" - the account\'s customer is suspended;<br>'
            '"customer_limited" - services are limited for the account\'s customer;<br>'
            '"customer_provisionally_terminated" - the account\'s customer is provisionally terminated;<br>'
            '"blocked" - the account is blocked;<br>'
            '"customer_blocked" - the account\'s customer is blocked;<br>'
            '"not_yet_active" - the account\'s activation date has not yet come;<br>'
            '"credit_exceeded" - the account\'s balance is above the individual credit limit;<br>'
            '"overdraft" - the account\'s balance is overdrawn (applies to debit accounts only);<br>'
            '"customer_has_no_available_funds" - the account\'s customer funds are depleted;<br>'
            '"customer_credit_exceed" - the account\'s customer balance is above the credit limit;<br>'
            '"zero_balance" - the account\'s funds are depleted (applicable to debit accounts only);<br>'
            '"customer_suspension_delayed" - the account\'s customer suspension is lifted;<br>'
            '"customer_limiting_delayed" - the account\'s customer limitation is delayed;<br>'
            '"frozen" - the account\'s auto-payment is suspended due to repeated errors.'
        ),
        examples=["active"]
    )
    time_zone_name: Optional[str] = Field(
        None,
        description=(
            "The name of the account's time zone. The UI equivalent of this field is the 'Time zone'. "
            'Examples: "Europe/Prague", "America/Vancouver", etc.'
        ),
        examples=["Europe/Kiev"]
    )
    zip: Optional[str] = Field(
        None,
        title="Zip code",
        description="The postal (zip) code",
        examples=["40004"]
    )
    assigned_addons: List[AddOnProduct] = Field(
        default_factory=list,
        description="The list of the account's add-on products"
    )
    service_features: List[ServiceFeature] = Field(
        default_factory=list,
        description="The list of the service features"
    )


class CardInfo(BaseModel):
    """SIM card information model"""
    i_account: Optional[int] = Field(
        None, 
        title="Account unique ID",
        description="The unique ID of the account to which the SIM card belongs",
        examples=[277147]
    )
    i_sim_card: Optional[int] = Field(
        None, 
        title="SIM Card ID",
        description="The unique ID of the SIM card",
        examples=[3793]
    )
    iccid: Optional[str] = Field(
        None, 
        title="ICCID",
        description=(
            "The Integrated Circuit Card ID. ICCIDs are stored in the SIM cards. "
            "Possible data format: a unique 18 to 22 digit code that includes the SIM card country, home network, and identification number."
        ),
        examples=["89014103211118510720"]
    )
    imsi: Optional[str] = Field(
        None,
        title="IMSI",
        description=(
            "The unique International Mobile Subscriber Identity of the SIM card. "
            "Possible data format: a string of 6 to 15 digits."
        ),  
        examples=["001010000020349"]
    )
    msisdn: Optional[str] = Field(
        None, 
        title="MSISDN",
        description="The Mobile Subscriber Integrated Services Digital Number, mobile number of the SIM card.",
        examples=["380661310764"]
    )
    status: Optional[str] = Field(
        None,
        description="The status of the SIM card",
        examples=["active"]
    )


class AccessPolicyAttribute(BaseModel):
    """Access policy attribute model"""
    group_name: Optional[str] = Field(
        None,
        description="The name used to group service policy attributes",
        examples=["lte.wtl"]
    )
    name: Optional[str] = Field(
        None,
        description="The name of the service policy attribute",
        examples=["cs_profile"]
    )
    value: Optional[str] = Field(
        None,
        description="Service policy attribute value, comma-separated if multiple values",
        examples=["cs-policy"]
    )


class AccessPolicyInfo(BaseModel):
    """Access policy information model"""
    i_access_policy: Optional[int] = Field(
        None,
        title="Access Policy ID",
        description="The unique ID of the Service Policy",
        examples=[179]
    )
    name: Optional[str] = Field(
        None,
        description="The name of the Access Policy",
        examples=["WTL integration"]
    )
    attributes: List[AccessPolicyAttribute] = Field(
        default_factory=list,
        description="The list of related service policy attribute values",
    )


class PBData(BaseModel):
    """PortaBilling data for event enrichment."""
    account_info: Optional[AccountInfo] = Field(
        None,
        description="Account information from PortaBilling"
    )
    sim_info: Optional[CardInfo] = Field(
        None,
        description="SIM card information from PortaBilling"
    )
    access_policy_info: Optional[AccessPolicyInfo] = Field(
        None,
        description="Access policy information from PortaBilling"
    )


class ESPFEvent(BaseModel):
    """Model representing incoming ESPF event"""
    event_type: str = Field(
        description="The type of the event",
        examples=["SIM/Updated"]
    )
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="All event variables passed as-is from original event",
    )


class Event(BaseModel):
    """Main event model"""
    event_id: str = Field(
        description="Unique identifier of the event",
        examples=["a3623086-24c2-47fb-a17f-929d9e542ed2"]
    )
    data: ESPFEvent = Field(
        description="Event data containing type and variables"
    )
    handler_id: Optional[str] = Field(
        None,
        description="ID of the handler processing this event",
        examples=["wtl"]
    )
    created_at: Optional[str] = Field(
        None,
        description="When the event was created (ISO datetime string)",
        examples=["2025-06-09T17:44:21.207629+00:00"]
    )
    updated_at: Optional[str] = Field(
        None,
        description="When the event was last updated (ISO datetime string)",
        examples=["2025-06-09T17:44:22.125109+00:00"]
    )
    status: Optional[str] = Field(
        None,
        description="Current status of the event",
        examples=["queued"]
    )
    pb_data: Optional[PBData] = Field(
        None,
        description="Simplified PortaBilling data with only essential fields"
    )


class EventResponse(BaseModel):
    """Event processing response"""
    message: str = "Event accepted for processing"