import socket
import select
from datetime import datetime
import time
import pickle
from PIL import Image
from deepface import DeepFace
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

## methods

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

def receive_message(client_socket):

    """
        receive message from a socket
    """
    try:
        in_msg = b""
        while True:
            packet = client_socket.recv(4096)
            if not packet: break
            in_msg += packet

        return in_msg
        #print(f"{datetime.fromtimestamp(time.time())}: saving image from {address}.")
        #timestamp = time.time()
        #img = pickle.loads(in_msg)
        

    except:
        return False
        #pass

## main logic

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
server_socket.bind((IP, PORT))
server_socket.listen(5)

sockets_list = [server_socket]
print(f"{datetime.fromtimestamp(time.time())}: App on line, listening at {IP}:{PORT}")

while True:
    # now our endpoint knows about the OTHER endpoint.
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
    
    # walk over notified sockets
    for notified_socket in read_sockets:
    
        # If notified socket is a server socket - new connection, accept it
        if notified_socket == server_socket:
            
            client_socket, client_address = server_socket.accept()
            user = receive_message(client_socket)

            if user is False:
                continue
                
            sockets_list.append(client_socket)

        ## receive message
        else:

            message = receive_message(notified_socket)

            if message is False:
                print(f'{datetime.fromtimestamp(time.time())}: connection closed from {client_address}')
            

                sockets_list.remove(notified_socket)
                continue
            
            else:

                timestamp = time.time()
                img = pickle.loads(message)
                tmp_img_path = f"{TMP_PATH}/img_{timestamp}.jpg"
                img.save(tmp_img_path)
    
                result = process_image(tmp_img_path,DB_PATH) 
                remove(tmp_img_path)
                notified_socket.send(bytes(result,'utf-8'))

    for notified_socket in exception_sockets:

        # remove from list for socket.socket()
        sockets_list.remove(notified_socket)
                
