"""
QUO.com API Integration
Complete messaging and communication platform integration
API Docs: https://www.quo.com/docs/mdx/api-reference/introduction
"""
import requests
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class QuoClient:
    """QUO.com API Client for messaging and communication"""

    def __init__(self, api_key: str, base_url: str = "https://api.quo.com/v1"):
        """
        Initialize QUO client

        Args:
            api_key: Your QUO API key
            base_url: QUO API base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        logger.info("QUO client initialized")

    # ==========================================
    # MESSAGING
    # ==========================================

    def send_message(
        self,
        to: str,
        message: str,
        channel: str = "sms",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a message via QUO

        Args:
            to: Recipient identifier (phone number, email, etc.)
            message: Message content
            channel: Channel type (sms, whatsapp, email, voice)
            **kwargs: Additional parameters

        Returns:
            API response dict
        """
        url = f"{self.base_url}/messages"

        payload = {
            "to": to,
            "message": message,
            "channel": channel,
            **kwargs
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            logger.info(f"Message sent to {to} via {channel}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message: {e}")
            raise

    def send_sms(self, to: str, message: str, from_number: Optional[str] = None) -> Dict[str, Any]:
        """Send SMS message"""
        payload = {
            "to": to,
            "message": message,
            "channel": "sms"
        }
        if from_number:
            payload["from"] = from_number

        return self.send_message(**payload)

    def send_whatsapp(
        self,
        to: str,
        message: str,
        media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp message

        Args:
            to: WhatsApp number (with country code)
            message: Message text
            media_url: Optional media URL (image, video, doc)
        """
        payload = {
            "to": to,
            "message": message,
            "channel": "whatsapp"
        }

        if media_url:
            payload["media"] = {"url": media_url}

        return self.send_message(**payload)

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send email via QUO

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body (HTML supported)
            from_email: Sender email
            attachments: List of attachment URLs
        """
        payload = {
            "to": to,
            "message": body,
            "channel": "email",
            "subject": subject
        }

        if from_email:
            payload["from"] = from_email

        if attachments:
            payload["attachments"] = attachments

        return self.send_message(**payload)

    # ==========================================
    # VOICE CALLS
    # ==========================================

    def make_call(
        self,
        to: str,
        message: str,
        voice: str = "en-US-female",
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make voice call with text-to-speech

        Args:
            to: Phone number to call
            message: Text to speak
            voice: Voice type
            callback_url: Webhook for call events
        """
        url = f"{self.base_url}/calls"

        payload = {
            "to": to,
            "message": message,
            "voice": voice
        }

        if callback_url:
            payload["callback_url"] = callback_url

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            logger.info(f"Call initiated to {to}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to make call: {e}")
            raise

    def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """Get status of a voice call"""
        url = f"{self.base_url}/calls/{call_id}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get call status: {e}")
            raise

    # ==========================================
    # CONVERSATIONS & THREADS
    # ==========================================

    def create_conversation(
        self,
        participants: List[str],
        channel: str = "sms"
    ) -> Dict[str, Any]:
        """
        Create a conversation thread

        Args:
            participants: List of participant identifiers
            channel: Channel type
        """
        url = f"{self.base_url}/conversations"

        payload = {
            "participants": participants,
            "channel": channel
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create conversation: {e}")
            raise

    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation details and messages"""
        url = f"{self.base_url}/conversations/{conversation_id}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get conversation: {e}")
            raise

    def send_conversation_message(
        self,
        conversation_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Send message to existing conversation"""
        url = f"{self.base_url}/conversations/{conversation_id}/messages"

        payload = {"message": message}

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send conversation message: {e}")
            raise

    # ==========================================
    # WEBHOOKS
    # ==========================================

    def create_webhook(
        self,
        url: str,
        events: List[str],
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create webhook for events

        Args:
            url: Webhook URL
            events: List of events to subscribe to
                   (e.g., ['message.received', 'call.completed'])
            name: Optional webhook name
        """
        webhook_url = f"{self.base_url}/webhooks"

        payload = {
            "url": url,
            "events": events
        }

        if name:
            payload["name"] = name

        try:
            response = requests.post(webhook_url, json=payload, headers=self.headers)
            response.raise_for_status()
            logger.info(f"Webhook created: {url}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create webhook: {e}")
            raise

    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all webhooks"""
        url = f"{self.base_url}/webhooks"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get("webhooks", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list webhooks: {e}")
            raise

    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        url = f"{self.base_url}/webhooks/{webhook_id}"

        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            logger.info(f"Webhook deleted: {webhook_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete webhook: {e}")
            return False

    # ==========================================
    # TEMPLATES
    # ==========================================

    def send_template(
        self,
        to: str,
        template_id: str,
        variables: Dict[str, str],
        channel: str = "whatsapp"
    ) -> Dict[str, Any]:
        """
        Send template message

        Args:
            to: Recipient
            template_id: Template identifier
            variables: Template variables
            channel: Channel type
        """
        url = f"{self.base_url}/messages/template"

        payload = {
            "to": to,
            "template_id": template_id,
            "variables": variables,
            "channel": channel
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send template: {e}")
            raise

    # ==========================================
    # ANALYTICS & REPORTING
    # ==========================================

    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Get message delivery status"""
        url = f"{self.base_url}/messages/{message_id}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get message status: {e}")
            raise

    def get_analytics(
        self,
        start_date: str,
        end_date: str,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get analytics data

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            channel: Optional channel filter
        """
        url = f"{self.base_url}/analytics"

        params = {
            "start_date": start_date,
            "end_date": end_date
        }

        if channel:
            params["channel"] = channel

        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get analytics: {e}")
            raise

    # ==========================================
    # UTILITY METHODS
    # ==========================================

    def validate_phone(self, phone_number: str) -> Dict[str, Any]:
        """Validate phone number format"""
        url = f"{self.base_url}/validate/phone"

        payload = {"phone": phone_number}

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to validate phone: {e}")
            raise

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information and balance"""
        url = f"{self.base_url}/account"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get account info: {e}")
            raise


# ==========================================
# INTEGRATION WITH RAGBOT
# ==========================================

class QuoBot:
    """QUO Bot integrated with RAG system"""

    def __init__(self, quo_api_key: str, rag_system):
        self.client = QuoClient(quo_api_key)
        self.rag_system = rag_system
        logger.info("QuoBot initialized")

    def handle_incoming_message(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming message from QUO webhook

        Webhook format:
        {
            "event": "message.received",
            "message_id": "msg_xxx",
            "from": "447123456789",
            "to": "441234567890",
            "channel": "whatsapp",
            "content": {
                "text": "Hello"
            },
            "timestamp": "2024-01-01T12:00:00Z"
        }
        """
        try:
            event = webhook_data.get("event")

            if event == "message.received":
                from_number = webhook_data.get("from")
                channel = webhook_data.get("channel")
                content = webhook_data.get("content", {})
                message_text = content.get("text", "")

                # Process with RAG system
                response = self.rag_system.query_with_context(from_number, message_text)

                # Send response back via QUO
                if channel == "whatsapp":
                    self.client.send_whatsapp(from_number, response)
                elif channel == "sms":
                    self.client.send_sms(from_number, response)
                else:
                    self.client.send_message(from_number, response, channel=channel)

                return {"status": "success", "response": response}

            return {"status": "event_not_handled"}

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # Test the client
    import os

    api_key = os.getenv("QUO_API_KEY", "your_quo_api_key_here")

    if api_key:
        client = QuoClient(api_key)
        print("✅ QUO client initialized successfully")

        # Test account info
        try:
            account = client.get_account_info()
            print(f"Account: {account}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("❌ Missing QUO_API_KEY environment variable")
