from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from ..services.wtl_client import WTLClient, WTLError
from ..services.pb_event import PortaBillingEventProcessor
from ..models.events import BillStatus
from ..models.wtl import UnifiedSyncRequest, SubscriberStatus, EventWTLActionMapper
from ..core.logging import get_logger

logger = get_logger(__name__)

class EventProcessor:
    def __init__(self):
        self.wtl_client = WTLClient()

    def process_event(self, event_data):
        """Process incoming PortaBilling ESPF event"""
        try:
            processor = PortaBillingEventProcessor(event=event_data)

            logger.info(f"Received event: {event_data.event_id}, type: {event_data.data.event_type}")

            action = EventWTLActionMapper(
                event_type=processor.get_event_type()
            ).action

            if not action:
                message = f"No defined action for event type: {processor.get_event_type()}"
                logger.warning(message)
                return JSONResponse(
                    content={"message": f"Event ignored: {message}"},
                    status_code=status.HTTP_202_ACCEPTED
                )

            imsi = processor.get_imsi_from_sim_info()
            if not imsi:
                message = "IMSI is empty or not provided"
                logger.warning(message)
                return JSONResponse(
                    content={"message": f"Event ignored: {message}"},
                    status_code=status.HTTP_202_ACCEPTED
                )

            if not processor.validate_imsi_using_regex(imsi):
                message = f"IMSI {imsi} doesn't follow the regexp provided"
                logger.warning(message)
                return JSONResponse(
                    content={"message": f"Event ignored: {message}"},
                    status_code=status.HTTP_202_ACCEPTED
                )

            msisdn_list = []
            if processor.get_bill_status() == BillStatus.OPEN.value:
                msisdn_list = [processor.get_account_id()]

            subscriber_status = SubscriberStatus.OPERATOR_DETERMINED_BARRING.value
            if (
                not processor.get_block_status()
                and processor.get_bill_status() == BillStatus.OPEN.value
            ):
                subscriber_status = SubscriberStatus.SERVICE_GRANTED.value

            # Create and send unified request
            request_data = UnifiedSyncRequest(
                imsi=imsi,
                subscriber_status=subscriber_status,
                msisdn=msisdn_list,
                cs_profile=processor.get_cs_profile(),
                eps_profile=processor.get_eps_profile(),
                action=action,
            )

            logger.info(
                "Sending unified sync request",
                extra={
                    "event_id": event_data.event_id,
                    "imsi": request_data.imsi,
                    "status": request_data.subscriber_status,
                    "msisdn": request_data.msisdn,
                    "cs_profile": request_data.cs_profile,
                    "eps_profile": request_data.eps_profile,
                    "action": action,
                },
            )

            self.wtl_client.send_request(request_data)
            return JSONResponse(
                content={"message": "Event processed successfully"},
                status_code=status.HTTP_202_ACCEPTED
            )

        except WTLError as e:
            logger.error(f"WTL error: {e.error_response.error}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.error_response.model_dump()
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": "Internal server error", "error": str(e)}
            )