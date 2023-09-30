from deepface import DeepFace


recognition = DeepFace.verify(img1_path="./app/data/test_img/Bono_0001.jpg",
                              img2_path="./app/data/test_img/Brad_Pitt_0001.jpg"
                              )
print(recognition)

