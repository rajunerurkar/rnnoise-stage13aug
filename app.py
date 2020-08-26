from flask import Flask
from flask import request
import rnn_noise_wav

app = Flask(__name__)

 
@app.route('/')
def hello():
    return "Hello World!"

@app.route('/data')
def data():
    # here we want to get the value of user (i.e. ?user=some-value)
    file_name = request.args.get('fname')
    wav_byte= rnn_noise_wav.rnnoiseTest(file_name)
    print("Successfully run!"+file_name)
    return str(wav_byte)
if __name__ == '__main__':
    app.run()

