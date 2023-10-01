import socket
from datetime import datetime
import time
import pickle
from PIL import Image
from deepface import DeepFace
import threading  # Import the threading module

import argparse
import pandas as pd
import time
import sqlite3
import math
from os import remove

parser = argparse.ArgumentParser()
parser.add_argument("-p","--port", type=int, help="TCP/IP port",
                    required=True)
parser.add_argument("-i","--ip_direction", type=str, help="ip direction",
                    required=True)
parser.add_argument("-d","--db_path", type=str, help='sqlite db to compare',
                    required=True)
parser.add_argument("-t","--temporal_path", type=str, help='folder to store the temporal \'downloaded\' images',
                    required=True)

args = parser.parse_args()
cli_arguments = vars(args)


# Data parameters
DB_PATH = cli_arguments['db_path']

# Ordering parameters
TMP_PATH = cli_arguments['temporal_path']

# Networking parameters
PORT = cli_arguments['port']
IP = cli_arguments['ip_direction']

def process_image(target_img_path,db_path) -> str:

    """
        returns the analysis from the passed image as a str
    
    """


    try:
        #target_img = DeepFace.extract_faces(img_path = target_img_path)[0]["face"]
        target_embedding = DeepFace.represent(img_path = target_img_path, model_name = "Facenet")[0]["embedding"]

        # perform sentyment analisis
        analysis = DeepFace.analyze(img_path = target_img_path,
            #actions = ['age', 'gender', 'race', 'emotion']
            actions = ['emotion']
        )
        analysis = analysis[0]  # keep just the first register (it just show only have one)


        # database connection and data loading
        conn = sqlite3.connect(db_path)
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
        conn.close()

        result_df = pd.DataFrame(instances, columns = ["img_name", "distance", "person_name"])
        

        if not result_df.empty:
            # if df is not empty there was a matching result
            #print(result_df["person_name"].head(1))
            identity = str(result_df['person_name'])
            identity = identity.replace('_',' ')
            match = str(result_df['img_name'])

        else:
            # there was not result
            #print("person was not found on employees database")
            identity = '<Unknown>'
            match = 'N/A'


        ## sentiment analysis
         
        result = f'''\n
        =================RESULTS=================
        \nReport:
            ├Identity:
            │    ├Human name:        {identity}
            │    └image path:        {match}
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
            '''
        return result

    except ValueError:
        #print("No face detected")
        return "No face detected"

def handle_client(client_socket):
    try:
        in_msg = b""
        while True:
            packet = client_socket.recv(4096)
            if not packet:
                break
            in_msg += packet

        client_socket.send("image received".encode('utf-8'))
        print(f"{datetime.fromtimestamp(time.time())}: saving image from {address}.")
        timestamp = time.time()
        img = pickle.loads(in_msg)

        # process the image
        tmp_img_path = f"{TMP_PATH}/img_{timestamp}.jpg"
        img.save(tmp_img_path)
        out_message = process_image(tmp_img_path, DB_PATH)
        remove(tmp_img_path)
        print(out_message)
        #
        client_socket.sendall(bytes(out_message, "utf-8"))

        print(f"{datetime.fromtimestamp(time.time())}: request from {address} has been solved.")
    except Exception as e:
        print(f"Error processing client request: {e}")
    finally:
        client_socket.close()

try: 
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    server_socket.bind((IP, PORT))
    server_socket.listen(5)


    print(f"{datetime.fromtimestamp(time.time())}: App on line at {IP}:{PORT}")

    while True:
        client_socket, address = server_socket.accept()
        print(f"{datetime.fromtimestamp(time.time())}: Connection from {address} has been established.")

        # Create a new thread to handle the client connection
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()
except KeyboardInterrupt:
    server_socket.close()
    print("closing...")