from pymongo import MongoClient

def connect_to_mongo(uri: str, database_name: str):
    """
    Connect to a MongoDB database.

    :param uri: MongoDB connection URI.
    :param database_name: Name of the database to connect to.
    :return: The database object.
    """
    try:
        # Create a MongoClient instance
        client = MongoClient(uri)
        
        # Access the specified database
        db = client[database_name]
        
        print(f"Connected to MongoDB database: {database_name}")
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None
