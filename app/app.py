from deepface import DeepFace
import sqlite3
import os

#verification = DeepFace.verify(img1_path = "../data/test_img/Bono_0001.jpg", img2_path = "../data/test_img/Brad_Pitt_0001.jpg")
#print(verification)

conn = sqlite3.connect('./data/facialdb.db')
cursor = conn.cursor()

#recognition = DeepFace.find(img_path= "../data/test_img/Bono_0001.jpg", db_path="~/jairojg/venv/data/facialdb.db")
recognition = DeepFace.find(img_path= "./data/test_img/Bono_0001.jpg", db_path="./data/test_db",enforce_detection=False)
print(recognition)

