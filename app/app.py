from deepface import DeepFace
import pandas as pd
import time
import sqlite3
import math

# reading image and extracting embeddings
target_img_path = 'data/test_img/Bono_0001.jpg'
target_img = DeepFace.extract_faces(img_path = target_img_path)[0]["face"]
target_embedding = DeepFace.represent(img_path = target_img_path, model_name = "Facenet")[0]["embedding"]


# database connection and data loading
conn = sqlite3.connect('./data/facialdb.db')
cursor = conn.cursor()

######################

target_statement = ''
for i, value in enumerate(target_embedding):
    target_statement += 'select %d as dimension, %s as value' % (i, str(value)) #sqlite
     
    if i < len(target_embedding) - 1:
        target_statement += ' union all '


select_statement = f'''
    select * 
    from (
        select img_name, sum(subtract_dims) as distance_squared, person_name
        from (
            select img_name, (source - target) * (source - target) as subtract_dims, person_name
            from (
                select meta.img_name, emb.value as source, target.value as target, meta.person_name
                from face_meta meta left join face_embeddings emb
                on meta.id = emb.face_id
                left join (
                    {target_statement}  
                ) target
                on emb.dimension = target.dimension
            )
        )
        group by img_name
    )
    where distance_squared < 100
    order by distance_squared asc
'''


tic = time.time()
results = cursor.execute(select_statement)


print(results)

instances = []
for result in results:
    img_name = result[0]
    distance_squared = result[1]
    person_name = result[2]

    instance = []
    instance.append(img_name)
    instance.append(math.sqrt(distance_squared))
    instance.append(person_name)
    instances.append(instance)

toc = time.time()
print(toc-tic,"seconds")

result_df = pd.DataFrame(instances, columns = ["img_name", "distance", "person_name"])

print(result_df["person_name"].head(1))