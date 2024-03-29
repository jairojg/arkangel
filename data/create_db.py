import sqlite3
#from deepface.commons import functions
from deepface import DeepFace
import pandas as pd
from tqdm import tqdm
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('-d','--root_directory', type = str, 
                    help = 'Images root directory',required=True)
parser.add_argument('-o','--output_path', type = str,
                     help = 'path to save the db',required=True)
args = parser.parse_args()
cli_arguments = vars(args)


# defining main parameters

root = cli_arguments['root_directory']
db_path = cli_arguments['output_path']

#root = "./data/test_db/"
#db_path = './data/facialdb.db'

# extracting embeddings and formatting the data
instances = []
names = os.listdir(root)
#names = names[0:50]

print(f"db_creator: Trying to faces from {root}")
log = ""

for name in tqdm(names):

    person_root = "{}{}/".format(root,name)

    for filename in os.listdir(person_root):
        
        try:
            
            #print(filename)
            facefile = "{}{}".format(person_root,filename)
            embedding = DeepFace.represent(img_path=facefile, model_name = "Facenet")[0]["embedding"]        

            instance = []
            instance.append(name)
            instance.append(facefile)
            instance.append(embedding)
            instances.append(instance)

        except:
            log += "\n\t├No face found on {}".format(filename)
            
df = pd.DataFrame(instances, columns = ["person_name",'img_name', 'embedding'])

print(f"db_creator: faces extracted, trying to save to sqlite.")

# conection to db
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
## deleting previous iterations
cursor.execute('''drop table if exists face_meta''')
cursor.execute('''drop table if exists face_embeddings''')
## define the sctructure
cursor.execute('''create table face_meta (ID INT primary key, PERSON_NAME VARCHAR(30), IMG_NAME VARCHAR(15), EMBEDDING BLOB)''')
cursor.execute('''create table face_embeddings (FACE_ID INT, DIMENSION INT, VALUE DECIMAL(10, 30))''')


# saving to sqlite 
for index, instance in tqdm(df.iterrows(), total=df.shape[0]):
    img_name = instance['img_name']
    person_name = instance["person_name"] 
    embeddings = instance['embedding']
    
    insert_statement = 'INSERT INTO face_meta (ID, PERSON_NAME, IMG_NAME, EMBEDDING) VALUES (?, ?, ?, ?)'
    insert_args = (index, person_name, img_name, str(embeddings))
    cursor.execute(insert_statement, insert_args)
     
    for i, embedding in enumerate(embeddings):
        insert_statement = 'INSERT INTO face_embeddings (FACE_ID, DIMENSION, VALUE) VALUES (?, ?, ?)'
        insert_args = (index, i, str(embedding))
        cursor.execute(insert_statement, insert_args)

conn.commit()
conn.close()

if log == '':
    log = '\n\t├No errors found'


print(f'''\ndb_creator: 
    \t└Log:{log}
    \t└End''')


print(f"db_creator: saving finalized to {db_path}")
