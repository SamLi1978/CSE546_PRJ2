from fileinput import filename
from flask import *
import os
import time

image_uploaded_dir = './images_uploaded'
pipe_name = "my_pipe"

app = Flask(__name__)

def notify_server(pipe_name, image_name):
    try:
        pipe = os.open(pipe_name, os.O_RDWR | os.O_NONBLOCK)
        tx_str = image_name
        for i in range(20-len(image_name)):
            tx_str = tx_str + "\n"
        msg_bytes = bytes(tx_str, 'utf-8')
        os.write(pipe, msg_bytes)
        os.close(pipe)
        return True

    except FileNotFoundError:
        return False

@app.route('/')
def index():
	return "CSE546 Web Server Instance"

@app.route('/', methods=['POST'])
def upload_file():
	if request.method == 'POST':
		uploaded_file = request.files['myfile']
		if uploaded_file.filename != '':
			dir = os.path.isdir(image_uploaded_dir)
			if dir == False:
				os.mkdir(image_uploaded_dir)
			uploaded_file.save("{}/{}".format(image_uploaded_dir,uploaded_file.filename))
			output = "{} uploaded".format(uploaded_file.filename)
			print(output)
			notify_server(pipe_name, uploaded_file.filename)
			return output
		else:
			return "Invalid file name" 

if __name__=="__main__":

    app.run(debug=True, host="0.0.0.0", port=8080)

