from typing import Any, Dict, Type, Union

from google.cloud.firestore_v1 import SERVER_TIMESTAMP
from pydantic import BaseModel

from shared.firebase_client import firebase_client


class FirestoreSyncMixin:
    """Reusable mixin to simplify Firestore create/update with Pydantic models + timestamps."""

    collection_name: str  # must be set in subclasses
    model: Type[BaseModel]  # enforce structure

    @classmethod
    def _get_ref(cls, doc_id: str):
        return (
            firebase_client.get_firestore()
            .collection(cls.collection_name)
            .document(doc_id)
        )

    @classmethod
    def sync(
        cls, doc_id: str, data: Union[Dict[str, Any], BaseModel], create: bool = False
    ):
        """
        Create or update a document.
        - Accepts either dict or Pydantic model.
        - Always updates `updatedAt`.
        - Optionally sets `createdAt`.
        """
        # Convert to dict if it's a Pydantic model
        if isinstance(data, BaseModel):
            payload = data.model_dump()
        else:
            payload = dict(data)

        payload["updatedAt"] = SERVER_TIMESTAMP
        if create:
            payload["createdAt"] = SERVER_TIMESTAMP

        ref = cls._get_ref(doc_id)
        ref.set(payload, merge=True)
        return ref

    @classmethod
    def get(cls, doc_id: str) -> BaseModel:
        """
        Fetch doc and parse back into the Pydantic model.
        """
        ref = cls._get_ref(doc_id).get()
        if ref.exists:
            return cls.model(**ref.to_dict())
        return None
