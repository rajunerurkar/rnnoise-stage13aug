import wave
import os,sys
import ctypes
import contextlib
import numpy as np
from ctypes import util
from scipy.io import wavfile
from pydub import AudioSegment
import logging
#import pandas as pd

#loading libraries and setting up the environment

# borrowed from here 
# https://github.com/Shb742/rnnoise_python
class RNNoise(object):

    def __init__(self,lib_path):
     self.lib = ctypes.cdll.LoadLibrary(lib_path)
     self.lib.rnnoise_process_frame.argtypes =[ctypes.c_void_p,ctypes.POINTER(ctypes.c_float),ctypes.POINTER(ctypes.c_float)]
     self.lib.rnnoise_process_frame.restype = ctypes.c_float
     self.lib.rnnoise_create.restype = ctypes.c_void_p
     self.lib.rnnoise_destroy.argtypes = [ctypes.c_void_p]
     self.obj = self.lib.rnnoise_create(None)
	
    def process_frame(self,inbuf):
     outbuf = np.ndarray((480,), 'h', inbuf).astype(ctypes.c_float)
     outbuf_ptr = outbuf.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
     VodProb =  self.lib.rnnoise_process_frame(self.obj,outbuf_ptr,outbuf_ptr)
     return (VodProb,outbuf.astype(ctypes.c_short).tobytes())

    def destroy(self):
     self.lib.rnnoise_destroy(self.obj)
	
def read_wave(path):
    """Reads a .wav file.
    Takes the path, and returns (PCM audio data, sample rate).
    """
    with contextlib.closing(wave.open(path, 'rb')) as wf:
     num_channels = wf.getnchannels()
     assert num_channels == 1
     sample_width = wf.getsampwidth()
     assert sample_width == 2
     sample_rate = wf.getframerate()
     assert sample_rate in (8000, 16000, 32000, 48000)
     pcm_data = wf.readframes(wf.getnframes())
     return pcm_data, sample_rate        
    
      
def frame_generator(frame_duration_ms,
    audio,
    sample_rate):
    """Generates audio frames from PCM audio data.
    Takes the desired frame duration in milliseconds, the PCM data, 	and
    the sample rate.
    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
     yield audio[offset:offset + n]
     offset += n        
	

def rnnoiseTest(fname):
 logger = logging.getLogger('werkzeug') # grabs underlying WSGI logger
 handler = logging.FileHandler('test.log') # creates handler for the log file
 logger.addHandler(handler) # adds handler to the werkzeug WSGI logger


 print('Entry print in rrnoiseTest')
 #lib_path = util.find_library("rnnoise")
 #lib_path = util.find_library(".so.")
 #lib_path = "/app/.heroku/python/lib/librnnoise.so.0"
 lib_path = "/app/usr/local/lib/librnnoise.so.0"
 print('Library Path1:'+lib_path)	
 if (not("/" in lib_path)):
  lib_path = (os.popen('ldconfig -p | grep '+lib_path).read().split('\n')[0].strip().split(" ")[-1] or ("/usr/local/lib/"+lib_path))

 logging.warning('Library Path:'+lib_path)
 print('Library Path2:'+lib_path)	
 denoiser = RNNoise(lib_path)      

 import sys
 import shutil
 #file_name=sys.argv[1]
 file_name=fname
 #file_name='overlayed_noisy_sounds/9.wav'
 wav_path=file_name

 TARGET_SR = 48000
 TEMP_FILE = 'test.wav'
 
 shutil.copyfile(file_name, 'abc_'+file_name)
 
 sound = AudioSegment.from_wav(wav_path)
 sound = sound.set_frame_rate(TARGET_SR)
 sound = sound.set_channels(1)

 sound.export(TEMP_FILE,
	     format="wav")
 logging.warning('Export done!')
 audio, sample_rate = read_wave(TEMP_FILE)
 assert sample_rate == TARGET_SR
 frames = frame_generator(10, audio, TARGET_SR)
 frames = list(frames)
 tups = [denoiser.process_frame(frame) for frame in frames]
 denoised_frames = [tup[1] for tup in tups]
 logging.warning('denoised_frames done!')
 denoised_wav = np.concatenate([np.frombuffer(frame,
	                                     dtype=np.int16)
	                       for frame in denoised_frames])
 logging.warning('concatenate done!')
 wavfile.write(file_name.replace('.wav','_denoised.wav'),
	      TARGET_SR,
	      denoised_wav)
 logging.warning('file_name::'+str(file_name))
 logging.warning('file write done!'+str(TARGET_SR)+"---"+str(denoised_wav))
 return denoised_wav

