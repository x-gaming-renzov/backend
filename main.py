import os, dotenv

from src.utils.database import connect_to_mongo

dotenv.load_dotenv()

xg_mongo_db = connect_to_mongo(os.getenv('XG_MONGO_URI'), os.getenv('XG_MONGO_DB')) 

def check_task_required_completion():
    print('Checking tasks that require completion')

    # Get all tasks that require completion
    tasks = xg_mongo_db['tasks'].find({
        'status': 'active',
        'stage': 'active'
    })

    for task in tasks:
        if 'touched' in task:
            continue
        # add 'touched' field to task
        xg_mongo_db['tasks'].update_one({'_id': task['_id']}, {'$set': {'touched': True}})

        #TODO : start processing task
        