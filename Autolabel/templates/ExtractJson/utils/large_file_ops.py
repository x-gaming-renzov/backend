import os

def create_chunks(file_path, cache_path):
    with open(file_path, "r") as f:
        #read one line at a time till end of file
        data = f.readlines()
        for chunk_id, line in enumerate(data):
            #write each line to a new file
           with open(f"{cache_path}/chunks/chunk_{chunk_id}.txt", "w") as chunk_file:
                chunk_file.write(line)
    return chunk_id

    