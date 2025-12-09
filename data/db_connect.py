"""
All interaction with MongoDB should be through this file!
We may be required to use a new database at any point.
"""

import logging
import os
from functools import wraps
import certifi
from typing import Any, Callable, Dict, List, Optional

import pymongo as pm
from dotenv import load_dotenv
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from pymongo.results import InsertOneResult, UpdateResult

LOCAL = "0"
CLOUD = "1"

SE_DB = "seDB"

client = None

MONGO_ID = "_id"

DEFAULT_SERVER_SELECTION_TIMEOUT_MS = 5000
DEFAULT_CONNECT_TIMEOUT_MS = 5000
DEFAULT_SOCKET_TIMEOUT_MS = 20000  

logger = logging.getLogger(__name__)

load_dotenv()


def connect_db() -> pm.MongoClient:
    """
    This provides a uniform way to connect to the DB across all uses.
    Returns a mongo client object and sets the global client variable.
    
    Connection timeouts can be configured via environment variables:
    - MONGO_SERVER_SELECTION_TIMEOUT_MS (default: 5000ms)
    - MONGO_CONNECT_TIMEOUT_MS (default: 5000ms)
    - MONGO_SOCKET_TIMEOUT_MS (default: 20000ms)
    """
    global client
    if client is None:
        logger.info("Setting client because it is None.")
        
        # Get timeout settings from environment or use defaults
        server_selection_timeout_ms = int(
            os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", DEFAULT_SERVER_SELECTION_TIMEOUT_MS)
        )
        connect_timeout_ms = int(
            os.getenv("MONGO_CONNECT_TIMEOUT_MS", DEFAULT_CONNECT_TIMEOUT_MS)
        )
        socket_timeout_ms = int(
            os.getenv("MONGO_SOCKET_TIMEOUT_MS", DEFAULT_SOCKET_TIMEOUT_MS)
        )
        
        # Common connection options (timeouts only)
        base_connection_options = {
            "serverSelectionTimeoutMS": server_selection_timeout_ms,
            "connectTimeoutMS": connect_timeout_ms,
            "socketTimeoutMS": socket_timeout_ms,
        }
        
        if os.getenv("CLOUD_MONGO", LOCAL) == CLOUD:
            uri = os.getenv("ATLAS_MONGO_DB_URI")
            if not uri:
                raise ValueError(
                    "You must set your ATLAS_MONGO_DB_URI in cloud config."
                )
            else:
                logger.info("Connecting to Cloud Atlas MongoDB.")
                # Add TLS options for cloud connections
                cloud_connection_options = {
                    **base_connection_options,
                    "tlsCAFile": certifi.where()
                }
                client = pm.MongoClient(uri, **cloud_connection_options)
                logger.info("Successfully connected to Cloud Atlas MongoDB")
        else:
            mongo_uri = os.getenv("LOCAL_MONGO_DB_URI")
            if mongo_uri:
                redacted = mongo_uri
                if "@" in mongo_uri:
                    redacted = mongo_uri.split("@")[-1]
                logger.info(f"Connecting to Mongo locally using custom URI: {redacted}")
                # Local connections don't use TLS/SSL
                client = pm.MongoClient(mongo_uri, **base_connection_options)
                logger.info("Successfully connected to local MongoDB")
            else:
                # Default local connection without URI
                logger.info("Connecting to Mongo locally using default connection")
                client = pm.MongoClient("mongodb://localhost:27017/", **base_connection_options)
                logger.info("Successfully connected to local MongoDB")
    return client


def ensure_connection(func: Callable) -> Callable:
    """
    Decorator to ensure database connection exists before executing function.
    Automatically calls connect_db() if client is None.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        global client

        if client is None:
            client = connect_db()

        try:
            return func(*args, **kwargs)
        except (ConnectionFailure, ServerSelectionTimeoutError):
            logger.info("Connection lost. Reconnecting...")
            client = None
            client = connect_db()
            return func(*args, **kwargs)

    return wrapper


def convert_mongo_id(doc: dict) -> None:
    """
    Convert MongoDB ObjectId to string in-place for JSON serialization.
    """
    if MONGO_ID in doc:
        # Convert mongo ID to a string so it works as JSON
        doc[MONGO_ID] = str(doc[MONGO_ID])


@ensure_connection
def create(collection: str, doc: dict, db: str = SE_DB) -> InsertOneResult:
    """
    Insert a single doc into collection.
    """
    logger.debug(f"Creating document in collection '{collection}' of database '{db}'")
    return client[db][collection].insert_one(doc)


@ensure_connection
def read_one(collection: str, filt: dict, db: str = SE_DB) -> Optional[dict]:
    """
    Find with a filter and return on the first doc found.
    Return None if not found.
    """
    for doc in client[db][collection].find(filt):
        convert_mongo_id(doc)
        return doc
    return None


@ensure_connection
def delete(collection: str, filt: dict, db: str = SE_DB) -> int:
    """
    Delete a single document matching the filter.
    Returns the count of deleted documents (0 or 1).
    """
    logger.debug(f"Deleting document from collection '{collection}' with filter: {filt}")
    del_result = client[db][collection].delete_one(filt)
    return del_result.deleted_count


@ensure_connection
def delete_many(collection: str, filt: dict, db: str = SE_DB) -> int:
    """
    Delete multiple documents matching the filter.
    Returns the count of deleted documents.
    """
    result = client[db][collection].delete_many(filt)
    return result.deleted_count


@ensure_connection
def update(collection: str, filters: dict, update_dict: dict, db: str = SE_DB) -> UpdateResult:
    """
    Update a single document matching the filters.
    Uses $set operator to update specified fields.
    """
    return client[db][collection].update_one(filters, {"$set": update_dict})


def _apply_pagination(cursor: Any, limit: Optional[int] = None, offset: Optional[int] = None) -> Any:
    """
    Apply pagination (skip/limit) to a MongoDB cursor.
    """
    if offset is not None and offset > 0:
        cursor = cursor.skip(offset)
    if limit is not None and limit > 0:
        cursor = cursor.limit(limit)
    return cursor


@ensure_connection
def read(collection: str, db: str = SE_DB, no_id: bool = True, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Returns a list from the db with optional pagination.
    """
    ret = []
    cursor = client[db][collection].find()
    cursor = _apply_pagination(cursor, limit, offset)
    for doc in cursor:
        if no_id:
            if MONGO_ID in doc:
                del doc[MONGO_ID]
        else:
            convert_mongo_id(doc)
        ret.append(doc)
    return ret


@ensure_connection
def read_filtered(collection: str, filt: dict, db: str = SE_DB, no_id: bool = True,
                  limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Returns a filtered list from the db using the provided filt dict.
    """
    ret = []
    cursor = client[db][collection].find(filt)
    cursor = _apply_pagination(cursor, limit, offset)
    for doc in cursor:
        if no_id:
            if MONGO_ID in doc:
                del doc[MONGO_ID]
        else:
            convert_mongo_id(doc)
        ret.append(doc)
    return ret


def read_dict(collection: str, key: str, db: str = SE_DB, no_id: bool = True) -> Dict[str, Dict[str, Any]]:
    """
    Read all records from a collection and return as a dictionary
    keyed by the specified field.
    """
    recs = read(collection, db=db, no_id=no_id)
    recs_as_dict = {}
    for rec in recs:
        recs_as_dict[rec[key]] = rec
    return recs_as_dict


@ensure_connection
def fetch_all_as_dict(key: str, collection: str, db: str = SE_DB) -> Dict[str, Dict[str, Any]]:
    """
    Fetch all documents from a collection and return as a dictionary
    keyed by the specified field. Always removes _id field.
    """
    ret = {}
    for doc in client[db][collection].find():
        del doc[MONGO_ID]
        ret[doc[key]] = doc
    return ret
