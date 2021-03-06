from time import sleep
import pyaudio
import numpy as np

# set prams
CHUNK = 1024
INPUT_DEVICE1_INDEX = 1

class Decibel:
    def __init__(self,):
        self.pyaudio = pyaudio.PyAudio()
        self.stream = self.pyaudio.open(format = pyaudio.paInt16,
                        channels = int(self.pyaudio.get_device_info_by_index(INPUT_DEVICE1_INDEX)["maxInputChannels"]),
                        rate = int(self.pyaudio.get_device_info_by_index(INPUT_DEVICE1_INDEX)["defaultSampleRate"]),
                        input = True,
                        frames_per_buffer = CHUNK,
                        input_device_index = INPUT_DEVICE1_INDEX
                )
    def __del__(self):
        self.stream.close()
        self.pyaudio.terminate()

    def get_decibel(self)-> np.float64:
        data = np.empty(0)
        # for i in range(0, int(SAMPLING_RATE / CHUNK * RECORD_SECONDS)):
        elm = self.stream.read(CHUNK, exception_on_overflow = False)
        elm = np.frombuffer(elm, dtype="int16")/float((np.power(2,16)/2)-1)
        data = np.hstack([data, elm])
        # calc RMS
        rms = np.sqrt(np.mean([elm * elm for elm in data]))
        # RMS to db
        return to_db(rms, 20e-6)
    
    def monitor(self,callback,sec=1):
        pre = self.get_decibel()
        excess_counter = 2
        margin = 5
        while True:
            cur = self.get_decibel()
            print("{:.3f}".format(cur))
            if  abs(cur - pre) > margin:
                while excess_counter > 0:
                    cur = self.get_decibel()
                    print("{:.3f}".format(cur))
                    if abs(cur - pre) <= margin:
                        break
                    sleep(sec)
                    excess_counter -= 1
                if excess_counter == 0:
                    callback(pre,cur)
            pre = cur
            sleep(sec)

            
            
        

# amp to db
def to_db(x, base=1.0)-> np.float64:
    y=20*np.log10(x/base)
    return y