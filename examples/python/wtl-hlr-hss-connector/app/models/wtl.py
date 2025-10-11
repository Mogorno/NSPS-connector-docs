from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from .events import EventType


class WTLResponse(BaseModel):
    """WTL API response model"""

    result: Optional[bool] = Field(None, description="true if operation was successful")
    error: Optional[str] = Field(None, description="error message if result is false")
    message: Optional[str] = Field(None, description="response message")

    @property
    def is_successful(self) -> bool:
        """Check if the response indicates success"""
        # If result is explicitly set, use it
        if self.result is not None:
            return self.result

        # If only message is present (like in mock), consider it successful
        if self.message is not None and self.error is None:
            return True

        # If error is present, it's not successful
        if self.error is not None:
            return False

        # Default to True for backward compatibility
        return True


class WTLProvAction(str, Enum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    SET = "set"
    UNSET = "unset"
    MODIFY = "modify"


EVENT_ACTION_MAP = {
    EventType.SIM_UPDATED: WTLProvAction.UPDATE,
}


class EventWTLActionMapper(BaseModel):
    event_type: str

    @property
    def action(self) -> str:
        return EVENT_ACTION_MAP.get(self.event_type)


class WTLBaseRequest(BaseModel):
    """Base model for WTL API requests"""

    imsi: str = Field(..., pattern=r"^[0-9]{15}$", description="IMSI of the subscriber")


class SubscriberStatus(str, Enum):
    SERVICE_GRANTED = "serviceGranted"
    OPERATOR_DETERMINED_BARRING = "operatorDeterminedBarring"


class ServiceProfile(BaseModel):
    cs_profile: Optional[str] = Field(
        None, pattern=r"^[a-zA-Z][-_.a-zA-Z0-9]*$", description="CS profile name"
    )
    eps_profile: Optional[str] = Field(
        None, pattern=r"^[a-zA-Z][-_.a-zA-Z0-9]*$", description="EPS profile name"
    )


class MSISDNList(BaseModel):
    msisdn: List[str] = Field(
        ..., max_items=1, description="List of MSISDNs (max 1 item)"
    )


class StatusSyncRequest(WTLBaseRequest):
    """Request model for subscriber status synchronization"""

    subscriber_status: SubscriberStatus


class UnifiedSyncRequest(MSISDNList, ServiceProfile, StatusSyncRequest):
    """Request model for unified synchronization"""

    action: WTLProvAction = Field(
        default=WTLProvAction.UPDATE,
        title="Provisioning action",
    )