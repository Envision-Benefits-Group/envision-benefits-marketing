# src.ghl.ghl.py
import os
import traceback
from typing import List

import httpx
import structlog

# Initialize logger
logger = structlog.get_logger("GHL_SERVICE")


class GoHighLevelAPI:
    """
    A client class to interact with GoHighLevel's v1 and v2 APIs.
    It includes methods for:
    - Contact creation and retrieval (v1)
    - Uploading files to the media library (v2)
    """

    def __init__(self):
        # Load API keys from environment variables
        self.api_key_v1 = os.getenv("GHL_API_KEY")
        self.api_key_v2 = os.getenv(
            "GHL_API_KEY_V2"
        )  # v2 endpoints require a separate key
        # Validate API keys
        if not self.api_key_v1:
            logger.aerror("GHL_API_KEY environment variable not set.")
            raise ValueError("GHL_API_KEY environment variable not set.")
        # Define base URLs for API versions
        self.base_url_v1 = "https://rest.gohighlevel.com/v1"
        # Define default tag for all contacts
        self.default_tag = "free8up"
        logger.ainfo("GoHighLevelAPI initialized")

    async def find_contact(self, email: str):
        """
        Finds a contact by email.
        Parameters:
            email (str): The email address to search for.
        Returns:
            dict or None: The contact object if found, otherwise None.
        """
        await logger.ainfo(f"Searching for contact with email: {email}")
        url = f"{self.base_url_v1}/contacts/"
        headers = {
            "Authorization": f"Bearer {self.api_key_v1}",
            "Content-Type": "application/json",
        }
        params = {"query": email}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                contacts = response.json().get("contacts", [])
                for contact in contacts:
                    if contact.get("email") == email:
                        await logger.ainfo("Contact found")
                        return contact
                await logger.ainfo("No contact found for the given email")
                return None
            except httpx.HTTPError:
                tb_str = traceback.format_exc()
                await logger.aerror(
                    "HTTP error occurred while finding contact", error=tb_str
                )
                raise
            except Exception:
                tb_str = traceback.format_exc()
                await logger.aerror(
                    "An error occurred while finding contact", error=tb_str
                )
                raise

    async def create_contact(
        self, first_name: str, last_name: str, email: str, phone: str
    ):
        """
        Creates a new contact if one does not already exist with the given email,
        or retrieves the existing one. Automatically adds the default tag.
        Parameters:
            first_name (str): The contact's first name.
            last_name (str): The contact's last name.
            email (str): The contact's email address.
            phone (str): The contact's phone number.
        Returns:
            dict: The created or retrieved contact object.
        """
        await logger.ainfo(
            f"Attempting to create or retrieve contact with email: {email}"
        )
        existing_contact = await self.find_contact(email)
        if existing_contact:
            await logger.ainfo("Contact already exists, returning existing contact")
            return existing_contact
        url = f"{self.base_url_v1}/contacts/"
        headers = {
            "Authorization": f"Bearer {self.api_key_v1}",
            "Content-Type": "application/json",
        }
        payload = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phone": phone,
            "tags": [self.default_tag],  # Add default tag to all new contacts
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                await logger.ainfo("Contact created successfully with default tag")
                return response.json()
            except httpx.HTTPError:
                tb_str = traceback.format_exc()
                await logger.aerror(
                    "HTTP error occurred while creating contact", error=tb_str
                )
                raise
            except Exception:
                tb_str = traceback.format_exc()
                await logger.aerror(
                    "An error occurred while creating contact", error=tb_str
                )
                raise

    async def update_contact_with_email_change(
        self,
        old_email: str,
        new_email: str | None,
        first_name: str,
        last_name: str,
        phone: str,
    ) -> dict:
        """
        Updates a contact's information, properly handling email changes.
        If email is being changed, ensures all contact data and tags are preserved.
        
        Parameters:
            old_email (str): The contact's current email address
            new_email (str | None): The new email address (if being changed)
            first_name (str): The contact's first name
            last_name (str): The contact's last name
            phone (str): The contact's phone number
        Returns:
            dict: The updated contact object
        """
        try:
            # Find existing contact using old email
            contact = await self.find_contact(old_email)
            if not contact:
                await logger.ainfo(f"Contact with email {old_email} not found, creating new contact")
                return await self.create_contact(first_name, last_name, new_email or old_email, phone)

            contact_id = contact["id"]
            existing_tags = contact.get("tags", [])

            # If email is being changed, verify new email isn't already taken
            if new_email and new_email != old_email:
                existing_contact = await self.find_contact(new_email)
                if existing_contact:
                    await logger.aerror(f"Cannot update email: {new_email} already exists in GHL")
                    raise ValueError(f"Email {new_email} is already associated with another contact")

            # Prepare update payload according to GHL API specification
            payload = {
                "firstName": first_name,
                "lastName": last_name,
                "name": f"{first_name} {last_name}".strip(),  # Combined name as required by GHL
                "phone": phone,
                "tags": existing_tags,
                "source": "Scale8UP API"  # Identify source of the update
            }

            # Only include email in payload if it's being changed
            if new_email and new_email != old_email:
                payload["email"] = new_email

            # Preserve any existing fields from the contact
            for field in ["address1", "city", "state", "postalCode", "website", 
                         "timezone", "dnd", "customField", "companyName", "country"]:
                if field in contact and contact[field]:
                    payload[field] = contact[field]

            url = f"{self.base_url_v1}/contacts/{contact_id}"
            headers = {
                "Authorization": f"Bearer {self.api_key_v1}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                response = await client.put(url, json=payload, headers=headers)
                response.raise_for_status()
                await logger.ainfo(
                    f"Contact updated successfully. Old email: {old_email}, New email: {new_email if new_email else 'unchanged'}"
                )
                return response.json()

        except httpx.HTTPError:
            tb_str = traceback.format_exc()
            await logger.aerror(
                f"HTTP error occurred while updating contact {old_email}", error=tb_str
            )
            raise
        except Exception:
            tb_str = traceback.format_exc()
            await logger.aerror(
                f"An error occurred while updating contact {old_email}", error=tb_str
            )
            raise

    async def add_tags_to_contact(self, email: str, tags_to_add: List[str]):
        """
        Adds tags to an existing contact, avoiding duplicates.
        Parameters:
            email (str): The contact's email address.
            tags_to_add (List[str]): List of tags to add.
        Returns:
            dict: The updated contact object.
        """
        await logger.ainfo(f"Adding tags {tags_to_add} to contact with email: {email}")
        contact = await self.find_contact(email)
        if not contact:
            await logger.ainfo("Contact not found, cannot add tags")
            return None

        contact_id = contact["id"]
        existing_tags = contact.get("tags", [])

        # Check if any new tags need to be added
        new_tags = [tag for tag in tags_to_add if tag not in existing_tags]
        
        if not new_tags:
            await logger.ainfo(f"All tags already exist for contact {email}, skipping update")
            return contact

        # Merge existing tags with new tags, ensuring no duplicates
        updated_tags = list(set(existing_tags + new_tags))
        
        url = f"{self.base_url_v1}/contacts/{contact_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key_v1}",
            "Content-Type": "application/json",
        }
        payload = {"tags": updated_tags}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(url, json=payload, headers=headers)
                response.raise_for_status()
                await logger.ainfo(f"Added new tags {new_tags} to contact successfully")
                return response.json()
            except httpx.HTTPError:
                tb_str = traceback.format_exc()
                await logger.aerror(
                    "HTTP error occurred while updating contact tags", error=tb_str
                )
                raise
            except Exception:
                tb_str = traceback.format_exc()
                await logger.aerror(
                    "An error occurred while updating contact tags", error=tb_str
                )
                raise

    async def remove_tags_from_contact(self, email: str, tags_to_remove: List[str]):
        """
        Removes specified tags from a contact, avoiding duplicates.
        Finds the contact by email, filters out the tags_to_remove (case-insensitive),
        and updates the contact.
        """
        await logger.ainfo(f"Removing tags {tags_to_remove} from contact with email: {email}")
        contact = await self.find_contact(email)
        if not contact:
            await logger.ainfo(f"Contact not found for email {email}, cannot remove tags.")
            return None

        contact_id = contact["id"]
        existing_tags = contact.get("tags", [])
        removal_set = {tag.lower() for tag in tags_to_remove}
        updated_tags = [tag for tag in existing_tags if tag.lower() not in removal_set]

        if updated_tags == existing_tags:
            await logger.ainfo(f"No tags removed for contact {email}, tags remain unchanged.")
            return contact

        url = f"{self.base_url_v1}/contacts/{contact_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key_v1}",
            "Content-Type": "application/json",
        }
        payload = {"tags": updated_tags}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(url, json=payload, headers=headers)
                response.raise_for_status()
                await logger.ainfo(f"Removed tags {tags_to_remove} from contact {email} successfully.")
                return response.json()
            except httpx.HTTPError:
                tb_str = traceback.format_exc()
                await logger.aerror("HTTP error occurred while removing contact tags", error=tb_str)
                raise
            except Exception:
                tb_str = traceback.format_exc()
                await logger.aerror("An error occurred while removing contact tags", error=tb_str)
                raise

    async def create_contact_and_add_tags(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        tags_to_add: List[str],
    ):
        """
        Creates/retrieves a contact and then adds specified tags.
        This is a convenience method to chain contact creation and tag addition,
        making it suitable for background tasks.
        """
        await logger.ainfo(
            f"Processing contact for {email} with tags {tags_to_add}"
        )
        try:
            # This will create the contact with the default tag or retrieve it if it exists.
            contact = await self.create_contact(first_name, last_name, email, phone)

            # Then, we add the additional tags.
            if contact:
                await self.add_tags_to_contact(email, tags_to_add)
                await logger.ainfo(
                    f"Successfully processed contact {email} with tags {tags_to_add}"
                )
            else:
                # This path should ideally not be hit if create_contact raises exceptions on HTTP failure.
                await logger.aerror(
                    f"Failed to create/retrieve contact for {email}, cannot add tags."
                )
        except Exception:
            tb_str = traceback.format_exc()
            await logger.aerror(
                f"An error occurred in create_contact_and_add_tags for {email}",
                error=tb_str,
            )
            # Do not re-raise to prevent crashing background tasks. The error is logged.


if __name__ == "__main__":
    # Example usage
    # try:
    # Initialize the API client
    ghl_api = GoHighLevelAPI()
    # Create or retrieve a contact
    # contact = await ghl_api.create_contact(
    #     first_name="John",
    #     last_name="Doe",
    #     email="john.doe@example.com",
    #     phone="+1234567890",
    # )
    # print("Contact created or retrieved:", contact)
    pass
