from typing import Optional, List
import re

from ..core.config import settings
from ..core.logging import get_logger
from ..models.events import Event, BillStatus, AccessPolicyAttribute

logger = get_logger(__name__)


class PortaBillingEventProcessor:
    """PortaBilling Event processing"""

    def __init__(self, event: Event):
        self.event = event
        self.account_info = self.event and self.event.pb_data and self.event.pb_data.account_info
        self.access_policy_info = self.event and self.event.pb_data and self.event.pb_data.access_policy_info
        self.sim_info = self.event and self.event.pb_data and self.event.pb_data.sim_info

    def get_event_type(self) -> str:
        return self.event and self.event.data and self.event.data.event_type

    def get_imsi_from_sim_info(self) -> str:
        return self.sim_info and self.sim_info.imsi

    def validate_imsi_using_regex(self, imsi: str) -> bool:
        if settings.WTL_IMSI_REGEXP and not re.search(settings.WTL_IMSI_REGEXP, imsi):
            return False
        return True

    def get_account_id(self) -> Optional[str]:
        if not self.account_info:
            return None
        account_id = self.account_info.id
        return account_id.split("@msisdn")[0] if "@msisdn" in account_id else None

    def get_bill_status(self) -> Optional[BillStatus]:
        return self.account_info and self.account_info.bill_status

    def get_block_status(self) -> Optional[bool]:
        return self.account_info and self.account_info.blocked

    @staticmethod
    def _get_profile_value(
        attributes: List[AccessPolicyAttribute], name: str
    ) -> Optional[str]:
        for attr in attributes:
            if attr.name == name:
                return attr.value
        return None

    def _get_profile(self, profile_name: str, default_value: str) -> str:
        policy_info = self.access_policy_info
        if policy_info:
            profile = self._get_profile_value(policy_info.attributes, profile_name)
            if profile:
                return profile

        logger.info(
            f"Using default {profile_name} profile",
            extra={
                "event_id": self.event.event_id,
                "profile": default_value,
            },
        )
        return default_value

    def get_cs_profile(self) -> str:
        return self._get_profile("cs_profile", settings.WTL_DEFAULT_CS_PROFILE)

    def get_eps_profile(self) -> str:
        return self._get_profile("eps_profile", settings.WTL_DEFAULT_EPS_PROFILE)