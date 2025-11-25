"""
All interaction with MongoDB should be through this file!
We may be required to use a new database at any point.
"""

import logging
import os
from functools import wraps

import pymongo as pm
from dotenv import load_dotenv
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

LOCAL = "0"
CLOUD = "1"

SE_DB = "seDB"

client = None

MONGO_ID = "_id"

logger = logging.getLogger(__name__)

load_dotenv()


def connect_db():
    """
    This provides a uniform way to connect to the DB across all uses.
    Returns a mongo client object... maybe we shouldn't?
    Also set global client variable.
    We should probably either return a client OR set a
    client global.
    """
    global client
    if client is None:
        print("Setting client because it is None.")
        if os.getenv("CLOUD_MONGO", LOCAL) == CLOUD:
            uri = os.getenv("ALTAS_MONGO_DB_URI")
            if not uri:
                raise ValueError(
                    "You must set your ALTAS_MONGO_DB_URI in cloud config."
                )
            else:
                logger.info("Connecting to Cloud Atlas MongoDB.")
                client = pm.MongoClient(uri)
        else:
            mongo_uri = os.getenv("MONGO_URI")
            if mongo_uri:
                redacted = mongo_uri
                if "@" in mongo_uri:
                    redacted = mongo_uri.split("@")[-1]
                print(f"Connecting to Mongo locally using custom URI: {redacted}")
                client = pm.MongoClient(mongo_uri)
            else:
                logger.info("Connecting to Mongo locally on mongodb://localhost:27017.")
                client = pm.MongoClient("mongodb://localhost:27017")
    return client


def ensure_connection(func):
    """
    Decorator to ensure database connection exists before executing function.
    Automatically calls connect_db() if client is None.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
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


def convert_mongo_id(doc: dict):
    if MONGO_ID in doc:
        # Convert mongo ID to a string so it works as JSON
        doc[MONGO_ID] = str(doc[MONGO_ID])


@ensure_connection
def create(collection, doc, db=SE_DB):
    """
    Insert a single doc into collection.
    """
    print(f"{db=}")
    return client[db][collection].insert_one(doc)


@ensure_connection
def read_one(collection, filt, db=SE_DB):
    """
    Find with a filter and return on the first doc found.
    Return None if not found.
    """
    for doc in client[db][collection].find(filt):
        convert_mongo_id(doc)
        return doc


@ensure_connection
def delete(collection: str, filt: dict, db=SE_DB):
    """
    Find with a filter and return on the first doc found.
    """
    print(f"{filt=}")
    del_result = client[db][collection].delete_one(filt)
    return del_result.deleted_count


@ensure_connection
def delete_many(collection: str, filt: dict, db=SE_DB) -> int:
    """
    Delete multiple documents matching the filter.
    Returns the count of deleted documents.
    """
    result = client[db][collection].delete_many(filt)
    return result.deleted_count


@ensure_connection
def update(collection, filters, update_dict, db=SE_DB):
    return client[db][collection].update_one(filters, {"$set": update_dict})


@ensure_connection
def read(collection, db=SE_DB, no_id=True) -> list:
    """
    Returns a list from the db.
    """
    ret = []
    for doc in client[db][collection].find():
        if no_id:
            del doc[MONGO_ID]
        else:
            convert_mongo_id(doc)
        ret.append(doc)
    return ret


@ensure_connection
def read_filtered(collection, filt: dict, db=SE_DB, no_id=True) -> list:
    """
    Returns a filtered list from the db using the provided filt dict.
    """
    ret = []
    for doc in client[db][collection].find(filt):
        if no_id:
            if MONGO_ID in doc:
                del doc[MONGO_ID]
        else:
            convert_mongo_id(doc)
        ret.append(doc)
    return ret


def read_dict(collection, key, db=SE_DB, no_id=True) -> dict:
    recs = read(collection, db=db, no_id=no_id)
    recs_as_dict = {}
    for rec in recs:
        recs_as_dict[rec[key]] = rec
    return recs_as_dict


@ensure_connection
def fetch_all_as_dict(key, collection, db=SE_DB):
    ret = {}
    for doc in client[db][collection].find():
        del doc[MONGO_ID]
        ret[doc[key]] = doc
    return ret
