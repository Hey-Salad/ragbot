"""
Infobip Client for WhatsApp and SMS
Replaces Twilio with Infobip for better scalability
"""
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class InfobipClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infobip.com", timeout: float = 15.0):
        """
        Initialize Infobip client

        Args:
            api_key: Your Infobip API key
            base_url: Infobip API base URL (default: https://api.infobip.com)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.headers = {
            "Authorization": f"App {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _request(self, method: str, url: str, **kwargs):
        kwargs.setdefault("headers", self.headers)
        kwargs.setdefault("timeout", self.timeout)
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    def send_whatsapp_message(
        self,
        to: str,
        message: str,
        from_number: str
    ) -> Dict[str, Any]:
        """
        Send WhatsApp message via Infobip

        Args:
            to: Recipient phone number (e.g., '447123456789')
            message: Message text
            from_number: Your Infobip WhatsApp sender number

        Returns:
            API response dict
        """
        url = f"{self.base_url}/whatsapp/1/message/text"

        payload = {
            "from": from_number,
            "to": to,
            "content": {
                "text": message
            }
        }

        try:
            response = self._request("post", url, json=payload)
            response.raise_for_status()
            logger.info(f"WhatsApp message sent to {to}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            raise

    def send_whatsapp_template(
        self,
        to: str,
        from_number: str,
        template_name: str,
        template_data: Dict[str, str],
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Send WhatsApp template message

        Args:
            to: Recipient phone number
            from_number: Your Infobip WhatsApp sender
            template_name: Template name registered in Infobip
            template_data: Template variables
            language: Template language code
        """
        url = f"{self.base_url}/whatsapp/1/message/template"

        payload = {
            "from": from_number,
            "to": to,
            "content": {
                "templateName": template_name,
                "templateData": template_data,
                "language": language
            }
        }

        try:
            response = self._request("post", url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send template: {e}")
            raise

    def send_sms(
        self,
        to: str,
        message: str,
        from_sender: str = "HeySalad"
    ) -> Dict[str, Any]:
        """
        Send SMS via Infobip

        Args:
            to: Recipient phone number
            message: SMS text
            from_sender: Sender name or number
        """
        url = f"{self.base_url}/sms/2/text/advanced"

        payload = {
            "messages": [
                {
                    "from": from_sender,
                    "destinations": [
                        {"to": to}
                    ],
                    "text": message
                }
            ]
        }

        try:
            response = self._request("post", url, json=payload)
            response.raise_for_status()
            logger.info(f"SMS sent to {to}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send SMS: {e}")
            raise

    def get_whatsapp_messages(
        self,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get received WhatsApp messages

        Args:
            limit: Maximum number of messages to retrieve
        """
        url = f"{self.base_url}/whatsapp/1/inbox/messages"
        params = {"limit": limit}

        try:
            response = self._request("get", url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get messages: {e}")
            raise

    def send_whatsapp_image(
        self,
        to: str,
        from_number: str,
        image_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp image message

        Args:
            to: Recipient phone number
            from_number: Sender number
            image_url: URL of the image
            caption: Optional image caption
        """
        url = f"{self.base_url}/whatsapp/1/message/image"

        payload = {
            "from": from_number,
            "to": to,
            "content": {
                "mediaUrl": image_url
            }
        }

        if caption:
            payload["content"]["caption"] = caption

        try:
            response = self._request("post", url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send image: {e}")
            raise

    def send_whatsapp_document(
        self,
        to: str,
        from_number: str,
        document_url: str,
        filename: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp document

        Args:
            to: Recipient phone number
            from_number: Sender number
            document_url: URL of the document
            filename: Document filename
            caption: Optional caption
        """
        url = f"{self.base_url}/whatsapp/1/message/document"

        payload = {
            "from": from_number,
            "to": to,
            "content": {
                "mediaUrl": document_url,
                "filename": filename
            }
        }

        if caption:
            payload["content"]["caption"] = caption

        try:
            response = self._request("post", url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send document: {e}")
            raise

    def send_whatsapp_interactive_button(
        self,
        to: str,
        from_number: str,
        body_text: str,
        buttons: list,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send interactive button message

        Args:
            to: Recipient phone number
            from_number: Sender number
            body_text: Main message text
            buttons: List of button dicts with 'id' and 'title'
            header_text: Optional header
            footer_text: Optional footer
        """
        url = f"{self.base_url}/whatsapp/1/message/interactive/buttons"

        payload = {
            "from": from_number,
            "to": to,
            "content": {
                "body": {
                    "text": body_text
                },
                "action": {
                    "buttons": buttons
                }
            }
        }

        if header_text:
            payload["content"]["header"] = {"type": "TEXT", "text": header_text}
        if footer_text:
            payload["content"]["footer"] = {"text": footer_text}

        try:
            response = self._request("post", url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send interactive button: {e}")
            raise


if __name__ == "__main__":
    # Test the client
    import os

    api_key = os.getenv("INFOBIP_API_KEY")
    sender_number = os.getenv("INFOBIP_WHATSAPP_NUMBER")

    if api_key and sender_number:
        client = InfobipClient(api_key)
        print("✅ Infobip client initialized successfully")
        print(f"Base URL: {client.base_url}")
    else:
        print("❌ Missing environment variables:")
        print("   - INFOBIP_API_KEY")
        print("   - INFOBIP_WHATSAPP_NUMBER")
