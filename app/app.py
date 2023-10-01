from deepface import DeepFace
import pandas as pd
import time
import sqlite3
import math

# reading image and extracting embeddings
# target_img_path = 'data/test_img/ai.jpg' # face not found on db
# target_img_path = 'data/test_img/Blank_image.jpg' # face not found on image
# target_img_path = 'data/test_img/Ezra_miller.jpg' # face on image causes false positive 
#target_img_path = 'data/test_img/group.jpg' # group 
target_img_path = 'data/test_img/aaron_eckhart.jpg' #success A
target_img_path = 'data/test_img/Bono_0001.jpg' #success B

try:
    target_img = DeepFace.extract_faces(img_path = target_img_path)[0]["face"]
    target_embedding = DeepFace.represent(img_path = target_img_path, model_name = "Facenet")[0]["embedding"]

    # perform sentyment analisis
    analysis = DeepFace.analyze(img_path = target_img_path,
        #actions = ['age', 'gender', 'race', 'emotion']
        actions = ['emotion']
    )
    analysis = analysis[0]  # keep just the first register (it just show only have one)


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


    # Perform query
    tic = time.time()
    results = cursor.execute(select_statement)

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
    print("search finalizad in",toc-tic,"seconds")

    result_df = pd.DataFrame(instances, columns = ["img_name", "distance", "person_name"])
    

    if not result_df.empty:
        # if df is not empty there was a matching result
        #print(result_df["person_name"].head(1))
        print(str(result_df['person_name']))
        identity = str(result_df['person_name'])
        identity = identity.replace('_',' ')
        match = str(result_df['img_name'])

    else:
        # there was not result
        #print("person was not found on employees database")
        identity = '<Unknown>'
        match = 'N/A'


    ## sentiment analysis
    print(
    f'''\n
    =================RESULTS=================
    \nReport for: {target_img_path}
        ├Identity:
        │    ├Human name:        {identity}
        │    └image path:        {img_name}
        └Emotions:
            └Dominant emotion:  {analysis['dominant_emotion']}
                ├Angry:         {analysis['emotion']['angry']:0>7.3f}%
                ├Disgust:       {analysis['emotion']['disgust']:0>7.3f}%
                ├Fear:          {analysis['emotion']['fear']:0>7.3f}%
                ├Happy:         {analysis['emotion']['happy']:0>7.3f}%
                ├Sad:           {analysis['emotion']['sad']:0>7.3f}%
                ├Surprise:      {analysis['emotion']['surprise']:0>7.3f}%
                └Neutral:       {analysis['emotion']['neutral']:0>7.3f}%
    ========================================= 
        ''')

except ValueError:
    print("No face detected")

finally:
    print("Closing app")