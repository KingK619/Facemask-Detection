
import cv2
import imghdr
import os
import numpy as np 
import streamlit as st
from imutils import paths
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image,ImageEnhance
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from streamlit_webrtc import VideoTransformerBase, webrtc_streamer, ClientSettings
st.set_page_config(layout="wide")



DEFAULT_DATA_BASE_DIR='./'
IMAGE_DIR='demo/'
TEAM_DIR='team/'
prototxtPath = 'assets/deploy.prototxt.txt'
weightsPath= 'assets/res10_300x300_ssd_iter_140000.caffemodel'
net=cv2.dnn.readNet(weightsPath,prototxtPath)
model=load_model(r'assets/custom_4370_32_100_v2.h5')


# -------------------------- SIDE BAR --------------------------------
SIDEBAR_OPTION_WEBCAM = "Webcam Capture"
SIDEBAR_OPTION_UPLOAD_IMAGE = "Upload an Image"
SIDEBAR_OPTION_PROJECT_INFO = "Show Project Info"
SIDEBAR_OPTION_DEMO_IMAGE = "Select a Demo Image"
SIDEBAR_OPTION_MEET_TEAM = "Meet the Team"

SIDEBAR_OPTIONS = [SIDEBAR_OPTION_PROJECT_INFO,SIDEBAR_OPTION_UPLOAD_IMAGE,SIDEBAR_OPTION_WEBCAM,
                   SIDEBAR_OPTION_DEMO_IMAGE, SIDEBAR_OPTION_MEET_TEAM]

st.sidebar.image("assets/facemasklogo1.png")
st.sidebar.write(" ------ ")
st.sidebar.title("Explore the Following")


# --------------------------- Functions ----------------------------------

class VideoTransformer(VideoTransformerBase):
    def detect_and_predict_mask(self,frame1,net,model):
        #grab the dimensions of the frame and then construct a blob
        (h,w)=frame1.shape[:2]
        blob=cv2.dnn.blobFromImage(frame1,1.0,(300,300),(104.0,177.0,123.0))

        net.setInput(blob)
        detections=net.forward()

        #initialize our list of faces, their corresponding locations and list of predictions

        faces=[]
        locs=[]
        preds=[]


        for i in range(0,detections.shape[2]):
            confidence=detections[0,0,i,2]


            if confidence>0.7:
            #we need the X,Y coordinates
                box=detections[0,0,i,3:7]*np.array([w,h,w,h])
                (startX,startY,endX,endY)=box.astype('int')

                #ensure the bounding boxes fall within the dimensions of the frame
                (startX,startY)=(max(0,startX),max(0,startY))
                (endX,endY)=(min(w-1,endX), min(h-1,endY))

                #extract the face ROI, convert it from BGR to RGB channel, resize it to 224,224 and preprocess it
                face=frame1[startY:endY, startX:endX]
                face=cv2.cvtColor(face,cv2.COLOR_BGR2RGB)
                face=cv2.resize(face,(96,96))
                face=img_to_array(face)
                face=preprocess_input(face)

                faces.append(face)
                locs.append((startX,startY,endX,endY))

            #only make a predictions if atleast one face was detected
        if len(faces)>=1:
            faces=np.array(faces,dtype='float32')
            preds=model.predict(faces,batch_size=12)

        return (locs,preds)
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        net=cv2.dnn.readNet(weightsPath,prototxtPath)
        model=load_model(r'model/custom_4000_32_100.h5')
        (locs,preds)=self.detect_and_predict_mask(img,net,model)
        for (box,pred) in zip(locs,preds):
            (startX,startY,endX,endY)=box
            (mask,withoutMask)=pred
            label='Mask' if mask>withoutMask else 'No Mask'
            color=(0,255,0) if label=='Mask' else (0,0,255)
            #include the probability in the label
            label="{}: {:.2f}%".format(label,max(mask,withoutMask)*100)
            img=cv2.putText(img,label,(startX,startY-10),cv2.FONT_HERSHEY_SIMPLEX,0.45,color,2)
            img=cv2.rectangle(img,(startX,startY),(endX,endY),color,2)
        return img





def image_detections(img_path='./img/out.jpeg'):
    image=cv2.imread(img_path)
    #st.image(image_name)
    #st.text(type(image_name))
    #image=img_to_array(image_name)
    (h,w)=image.shape[:2]

    blob=cv2.dnn.blobFromImage(image,1.0,(300,300),(104.0,177.0,123.0))
    net.setInput(blob)
    detections = net.forward()
    # st.text(image.shape)
    #loop over the detections
    for i in range(0,detections.shape[2]):
        confidence=detections[0,0,i,2]
        if confidence>0.3:
            box=detections[0,0,i,3:7]*np.array([w,h,w,h])
            (startX,startY,endX,endY)=box.astype('int')
            (startX,startY)=(max(0,startX),max(0,startY))
            (endX,endY)=(min(w-1,endX), min(h-1,endY))
            face=image[startY:endY, startX:endX]
            face=cv2.cvtColor(face,cv2.COLOR_BGR2RGB)
            face=cv2.resize(face,(96,96))
            face=img_to_array(face)
            face=preprocess_input(face)
            face=np.expand_dims(face,axis=0)

            (withoutMask,mask)=model.predict(face)[0]
            # st.text(mask)
            # st.text(withoutMask)
            #determine the class label and color we will use to draw the bounding box and text
            label='Mask' if mask>withoutMask else 'No Mask'
            color=(0,255,0) if label=='Mask' else (255,0,0)
            #include the probability in the label
            label="{}: {:.2f}%".format(label,max(mask,withoutMask)*100)

            #display the label and bounding boxes
            cv2.putText(image,label,(startX,startY-10),cv2.FONT_HERSHEY_SIMPLEX,0.45,color,2)
            cv2.rectangle(image,(startX,startY),(endX,endY),color,2)
            
    return image



def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()





# ------------------------- Selection From SideBar ------------------

app_mode = st.sidebar.selectbox(
    "Please select from the following", SIDEBAR_OPTIONS)



if app_mode == SIDEBAR_OPTION_WEBCAM:
    st.text('In Develpment')
    ctx=webrtc_streamer(client_settings=ClientSettings(
                rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
                media_stream_constraints={"video": True, "audio": False},
                ),
                key="face-mask-detection", 
                video_transformer_factory=VideoTransformer
               )
   

elif app_mode == SIDEBAR_OPTION_UPLOAD_IMAGE:
    image_file = st.file_uploader("Upload Image", type=['png', 'jpeg', 'jpg'])
    if image_file is not None:
        # st.text(image_file.name)

        col1,col3 = st.beta_columns([30,30])
        
            
        enhance_type = st.sidebar.radio("Enhance Type",["Original","Gray-Scale","Contrast","Brightness"])
        img = Image.open(image_file)
        if enhance_type == 'Gray-Scale':
            img = np.array(img.convert('RGB'))
            img = cv2.cvtColor(img,1)
            img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            img = Image.fromarray(img)
        elif enhance_type == 'Contrast':
            c_rate = st.sidebar.slider("Contrast",0.5,3.5)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(c_rate)
        elif enhance_type == 'Brightness':
            c_rate = st.sidebar.slider("Brightness",0.5,3.5)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(c_rate)
               
        img = img.convert('RGB')
        saved_img = img.save('./img/out.jpeg')
        with col1:
            st.text("Orignal Image")
            st.image(img,caption="Input", use_column_width=True)
        st.sidebar.write('Please wait for the magic to happen! This may take up to a minute.')
        st.sidebar.info('PRIVACY POLICY: Uploaded images are never saved or stored. They are held entirely within memory for prediction \
        and discarded after the final results are displayed. ')
        with col3:
            st.text("Predicted Image")
            st.image(image_detections(),caption="Output", use_column_width=True)
    

elif app_mode == SIDEBAR_OPTION_DEMO_IMAGE:
    st.markdown("<h1 style='text-align: center; color: white;'>Select a Demo Image.</h1>", unsafe_allow_html=True)
    st.write("-------")
    col1,col3 = st.beta_columns([30,30])

    directory = os.path.join(DEFAULT_DATA_BASE_DIR, IMAGE_DIR)
    photos = []
    for file in os.listdir(directory):
        filepath = os.path.join(directory, file)

        # Find all valid images
        if imghdr.what(filepath) is not None:
            photos.append(file)

    photos.sort()

    option = st.sidebar.selectbox('Please select a sample image, then click Detect button', photos)

    st.empty()
    st.sidebar.write('Please wait for the detection to happen!')
    pic = os.path.join(directory, option)
    with col1:
        st.text("Orignal Image")
        st.image(pic,caption="Input", use_column_width=True)
    with col3:
        st.text("Predicted Image")
        st.image(image_detections(pic),caption="Output", use_column_width=True)

    
	    


elif app_mode == SIDEBAR_OPTION_PROJECT_INFO:
    st.sidebar.success("Project information showing on the right!")
    intro_markdown = read_markdown_file(os.path.join(DEFAULT_DATA_BASE_DIR,"README.md"))
    st.markdown(intro_markdown, unsafe_allow_html=True)

    


    
    
    
    
    
elif app_mode == SIDEBAR_OPTION_MEET_TEAM:
    st.sidebar.write(" ------ ")
    st.markdown("<h1 style='text-align: center; color: white;'>Team MASKD!</h1>", unsafe_allow_html=True)
    st.write("------")
    st.sidebar.write('Please feel free to connect with us on Linkedin!')
    st.sidebar.success('Hope you had a great time :)')
    col1,col2,col3 = st.beta_columns([2,2,2])
    with col1:
	    st.image(os.path.join(DEFAULT_DATA_BASE_DIR,TEAM_DIR,'kv.jpeg'),caption="Karanveer Sidana",use_column_width=True)
    with col2:
        st.image(os.path.join(DEFAULT_DATA_BASE_DIR,TEAM_DIR,'h2.jpeg'),caption="Hiten Goyal",use_column_width=True)
    with col3:
	    st.image(os.path.join(DEFAULT_DATA_BASE_DIR,TEAM_DIR,'channa.png'),caption="Charanjeet Singh",use_column_width=True)

    expandar_linkedin = st.beta_expander('Contact Information')
    expandar_linkedin.write(
        'Karan: https://www.linkedin.com/in/karanveer-sidana-07a49b1b1/')
    expandar_linkedin.write('Hiten: https://www.linkedin.com/in/hitengoyal/')
    expander_faq = st.beta_expander("More About Our Project")
    expander_faq.write("Hi there! If you have any questions about our project, or simply want to check out the source code, please visit our github repo: https://github.com/KingK619/Facemask-Detection")

else:
	raise ValueError(
        'Selected sidebar option is not implemented. Please open an issue on Github: ')

