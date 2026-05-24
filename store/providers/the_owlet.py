# providers/the_owlet.py

import requests
from django.conf import settings


class TheOwletAPI:
    BASE_URL = settings.API_URL  

    def __init__(self):
        self.api_key = settings.OWLET_API_KEY

    def create_order(self, service_id, link, quantity):
        """
        Create a new SMM order
        """

        payload = {
            "key": self.api_key,
            "action": "add",
            "service": service_id,
            "link": link,
            "quantity": quantity,
        }

        try:
            response = requests.post(
                self.BASE_URL,
                data=payload,
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            # Example successful response:
            # {
            #     "order": 23501
            # }

            if "order" in data:
                return {
                    "success": True,
                    "provider_order_id": data["order"],
                    "response": data,
                }

            return {
                "success": False,
                "error": data,
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
            }

    def get_order_status(self, provider_order_id):
        """
        Check status of an existing order
        """

        payload = {
            "key": self.api_key,
            "action": "status",
            "order": provider_order_id,
        }

        try:
            response = requests.post(
                self.BASE_URL,
                data=payload,
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            # Example response:
            # {
            #   "charge": "1.20",
            #   "start_count": "1200",
            #   "status": "Completed",
            #   "remains": "0"
            # }

            return {
                "success": True,
                "data": data,
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
            }

    def refill_order(self, provider_order_id):
        """
        Refill an order
        """

        payload = {
            "key": self.api_key,
            "action": "refill",
            "order": provider_order_id,
        }

        try:
            response = requests.post(
                self.BASE_URL,
                data=payload,
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            return {
                "success": True,
                "data": data,
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
            }

    def cancel_order(self, provider_order_id):
        """
        Cancel an order
        """

        payload = {
            "key": self.api_key,
            "action": "cancel",
            "order": provider_order_id,
        }

        try:
            response = requests.post(
                self.BASE_URL,
                data=payload,
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            return {
                "success": True,
                "data": data,
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
            }

    def get_balance(self):
        """
        Get provider account balance
        """

        payload = {
            "key": self.api_key,
            "action": "balance",
        }

        try:
            response = requests.post(
                self.BASE_URL,
                data=payload,
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            return {
                "success": True,
                "data": data,
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
            }