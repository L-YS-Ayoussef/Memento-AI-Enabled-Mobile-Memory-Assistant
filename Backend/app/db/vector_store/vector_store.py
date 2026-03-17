from datetime import datetime
from typing import Dict, Optional, Any, Tuple, List
import os, weaviate
from weaviate.classes.init import Auth
from weaviate.classes.tenants import Tenant
from weaviate.classes.query import Filter
from weaviate.agents.query import QueryAgent
from weaviate.agents.classes import QueryAgentCollectionConfig
from weaviate import WeaviateClient
from app.settings import settings
from app.agents.utils.helpers import add_timezone_to_datetime
from weaviate.exceptions import UnexpectedStatusCodeError, WeaviateInvalidInputError


class VectorStore:
    def __init__(self, headers=None):
        self.client: WeaviateClient = weaviate.connect_to_weaviate_cloud(
            cluster_url=settings.WEAVIATE_URL,
            auth_credentials=Auth.api_key(settings.WEAVIATE_API_KEY),
            headers=headers or {},
        )
        self._users = self.client.collections.get("User")
        self._events = self.client.collections.get("Event")

    def add_user(self, tenant_id: str):
        """Create matching tenant shards in both collections."""
        for col in (self._users, self._events):
            col.tenants.create([Tenant(name=tenant_id)])

    def add_user_general_information(self, tenant_id: str, text: str) -> str:
        try:
            return (
                self._users.with_tenant(tenant_id)
                .data.insert(properties={"general_information": text})
            )
        except UnexpectedStatusCodeError as e:
            raise ValueError(f"Tenant '{tenant_id}' not found") from e

    def add_event(
            self,
            tenant_id: str,
            event: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        """
        Insert an Event with refined conflict rules.

        Returns
        -------
        (True,  <uuid>)            on successful insert
        (False, dict | None)              when a blocking overlap exists
        """

        if event.get("cancelled", False):
            return True, self._insert_event(tenant_id, event)

        def _ts(key):
            v = event.get(key)
            return add_timezone_to_datetime(v) if v else None

        has_exact = event.get("start_time") and event.get("end_time")
        has_range = event.get("min_start_time") and event.get("max_end_time")

        if has_exact:
            new_start = _ts("start_time")
            new_end = _ts("end_time")
            window_type = "exact"
        elif has_range:
            new_start = _ts("min_start_time")
            new_end = _ts("max_end_time")
            window_type = "range"
        else:
            return True, self._insert_event(tenant_id, event)

        if new_start >= new_end:
            print("Ignoring insert: window start >= end")
            return False, None

        if event.get("can_overlap", False):
            return True, self._insert_event(tenant_id, event)

        if window_type == "exact":
            time_filter = (
                    Filter.by_property("start_time").less_or_equal(new_end)
                    & (Filter.by_property("end_time").greater_or_equal(new_start))
            )
        else:
            time_filter = (
                    Filter.by_property("min_start_time").less_or_equal(new_end)
                    & (Filter.by_property("max_end_time").greater_or_equal(new_start))
            )

        overlap_filter = (
                Filter.by_property("cancelled").equal(False)
                & (Filter.by_property("can_overlap").equal(False))
                & time_filter
        )

        try:
            conflicts = (
                self._events.with_tenant(tenant_id)
                .query.fetch_objects(
                    limit=1,
                    filters=overlap_filter,
                )
                .objects
            )
        except UnexpectedStatusCodeError:
            print(f"Tenant '{tenant_id}' missing or no permission")
            return False, None

        if conflicts:
            print(conflicts)
            c = conflicts[0].properties
            return False, conflicts[0].properties

        uuid = self._insert_event(tenant_id, event)
        return True, uuid

    def _insert_event(self, tenant_id: str, props: Dict[str, object]) -> str:
        return (
            self._events.with_tenant(tenant_id)
            .data.insert(properties=props)
        )

    def run_tenant_query(self, tenant_id: str, question: str):
        qa = QueryAgent(
            client=self.client,
            collections=[QueryAgentCollectionConfig(name="Event", tenant=tenant_id)],
        )
        try:
            return qa.run(question)
        except UnexpectedStatusCodeError as e:
            raise ValueError(f"Tenant '{tenant_id}' not found") from e

    def get_task_uuid(self, tenant_id: str, prompt: str) -> tuple[Any | None, str] | None:
        """
        Ask the Query Agent which Event the user means and return that
        Event's UUID (resp.sources[0].object_id).  If no match or the
        tenant is missing, return None.
        """
        agent = QueryAgent(
            client=self.client,
            collections=[QueryAgentCollectionConfig(name="Event", tenant=tenant_id)],
        )
        try:
            resp = agent.run(prompt)
        except UnexpectedStatusCodeError:
            return None
        if not resp.sources:
            return None, resp.final_answer
        first = resp.sources[0]
        uuid = getattr(first, "object_id", None) or first.get("object_id")

        return uuid, resp.final_answer

    def update_task_info(
            self,
            tenant_id: str,
            event_uuid: str,
            updates: Dict[str, Any],
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Partially update an Event and ensure the resulting schedule
        does not overlap other active, non-overlappable events.

        Returns
        --------
        (True,  None)                     → update succeeded
        (False, <conflict_properties>: dict)    → blocked by overlap
        """

        try:
            obj = (
                self._events.with_tenant(tenant_id)
                .query.fetch_objects(
                    limit=1,
                    filters=Filter.by_id().equal(event_uuid),
                )
                .objects
            )
            if not obj:
                return False, None
            current = obj[0].properties

        except UnexpectedStatusCodeError:
            return False, None

        merged = {**current, **updates}

        if merged.get("cancelled", False):
            try:
                self._events.with_tenant(tenant_id).data.update(
                    uuid=event_uuid, properties=updates
                )
                return True, None
            except WeaviateInvalidInputError:
                return False, None

        def _ts(key):
            ts = merged.get(key)
            return add_timezone_to_datetime(ts) if ts else None

        has_exact = merged.get("start_time") and merged.get("end_time")
        has_range = merged.get("min_start_time") and merged.get("max_end_time")

        if has_exact:
            new_start = _ts("start_time")
            new_end = _ts("end_time")
            time_filter = (
                    Filter.by_property("start_time").less_or_equal(new_end)
                    & (Filter.by_property("end_time").greater_or_equal(new_start))
            )
        elif has_range:
            new_start = _ts("min_start_time")
            new_end = _ts("max_end_time")
            time_filter = (
                    Filter.by_property("min_start_time").less_or_equal(new_end)
                    & (Filter.by_property("max_end_time").greater_or_equal(new_start))
            )
        else:
            try:
                self._events.with_tenant(tenant_id).data.update(
                    uuid=event_uuid, properties=updates
                )
                return True, None
            except WeaviateInvalidInputError:
                return False, None

        if merged.get("can_overlap", False):
            try:
                self._events.with_tenant(tenant_id).data.update(
                    uuid=event_uuid, properties=updates
                )
                return True, None
            except WeaviateInvalidInputError:
                return False, None

        overlap_filter = (
                Filter.by_id().not_equal(event_uuid)
                & (Filter.by_property("cancelled").equal(False))
                & (Filter.by_property("can_overlap").equal(False))
                & time_filter
        )

        conflicts = (
            self._events.with_tenant(tenant_id)
            .query.fetch_objects(
                limit=1,
                filters=overlap_filter,
            )
            .objects
        )

        if conflicts:
            return False, conflicts[0].properties
        try:
            self._events.with_tenant(tenant_id).data.update(
                uuid=event_uuid, properties=updates
            )
            return True, None
        except WeaviateInvalidInputError:
            return False, None

    def get_event_details(
            self, tenant_id: str, event_uuid: str
    ) -> tuple[bool, None] | Any:
        """
        Fetch a single Event by its UUID and return its properties dict,
        or None if not found or on error.
        """
        try:
            obj = (
                self._events.with_tenant(tenant_id)
                .query.fetch_objects(
                    limit=1,
                    filters=Filter.by_id().equal(event_uuid),
                )
                .objects
            )
            if not obj:
                return False, None
            current = obj[0].properties
        except UnexpectedStatusCodeError:
            return False, None
        return current

    def list_events_between(
        self,
        tenant_id: str,
        window_start: datetime | str,
        window_end: datetime | str,
    ) -> List[Dict[str, Any]]:
        """
        Return every **non-cancelled** event for the given tenant that
        overlaps the period [window_start, window_end] (inclusive).

        • Exact-window events (start_time / end_time) are included if
          start_time ≤ window_end  AND  end_time ≥ window_start.

        • Range-window events (min_start_time / max_end_time) are included if
          min_start_time ≤ window_end  AND  max_end_time ≥ window_start.

        Both string and aware-datetime inputs are accepted; they're
        normalised with add_timezone_to_datetime.
        """
        # Normalise & sanity-check the window
        # 1 ) normalise → RFC3339 text (your existing helper)
        ws_iso = add_timezone_to_datetime(window_start)
        we_iso = add_timezone_to_datetime(window_end)

        # 2 ) convert straight back to aware-datetime ─ the values
        #     we put in the filter below
        ws = datetime.fromisoformat(ws_iso)
        we = datetime.fromisoformat(we_iso)
        # Exact-window rule
        exact_filter = (
            Filter.by_property("start_time").less_or_equal(we)
            & Filter.by_property("end_time").greater_or_equal(ws)
        )
        # Range-window rule
        range_filter = (
            Filter.by_property("min_start_time").less_or_equal(we)
            & Filter.by_property("max_end_time").greater_or_equal(ws)
        )

        # Combine with OR, then exclude cancelled events
        events_filter = (
            (exact_filter | range_filter)
        )

        try:
            objs = (
                self._events.with_tenant(tenant_id)
                .query.fetch_objects(
                    limit=1000,           # raise / paginate if you expect >1000
                    filters=events_filter,
                )
                .objects
            )
            return [o.properties for o in objs]
        except UnexpectedStatusCodeError as e:
            raise ValueError(f"Tenant '{tenant_id}' not found") from e



vector_store = VectorStore()
