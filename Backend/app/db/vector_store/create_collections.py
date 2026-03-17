import weaviate
from weaviate.classes.init import Auth
import weaviate.classes.config as wc

from app.settings import settings

WCS_URL = settings.WEAVIATE_URL
WCS_KEY = settings.WEAVIATE_API_KEY

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WCS_URL,
    auth_credentials=Auth.api_key(WCS_KEY),
)


client.collections.create(
    name="User",
    vectorizer_config=wc.Configure.Vectorizer.text2vec_weaviate(),
    multi_tenancy_config=wc.Configure.multi_tenancy(
        enabled=True,
        auto_tenant_creation=False
    ),
    properties=[
        wc.Property(
            name="general_information",
            data_type=wc.DataType.TEXT
        ),
    ],
)


client.collections.create(
    name="Event",
    vectorizer_config=wc.Configure.Vectorizer.text2vec_weaviate(),
    multi_tenancy_config=wc.Configure.multi_tenancy(
        enabled=True,
        auto_tenant_creation=False
    ),
    properties=[
        wc.Property(name="title", data_type=wc.DataType.TEXT),
        wc.Property(name="trigger", data_type=wc.DataType.TEXT),
        wc.Property(name="start_time", data_type=wc.DataType.DATE),
        wc.Property(name="end_time", data_type=wc.DataType.DATE),
        wc.Property(name="min_start_time", data_type=wc.DataType.DATE),
        wc.Property(name="max_end_time", data_type=wc.DataType.DATE),
        wc.Property(name="can_overlap", data_type=wc.DataType.BOOL),
        wc.Property(name="recurring", data_type=wc.DataType.INT),
        wc.Property(name="place", data_type=wc.DataType.TEXT),
        wc.Property(name="people", data_type=wc.DataType.TEXT_ARRAY),
        wc.Property(name="details", data_type=wc.DataType.TEXT),
        wc.Property(name="cancelled", data_type=wc.DataType.BOOL),
    ],
)

client.close()