from time import sleep, time
import pigpio
import os
import json

FILE = os.path.normpath(os.path.join(os.path.abspath(__file__),"../../store"))

GPIO_IN = 18
GPIO_OUT = 17
POST_MS = 130
PRE_MS = 200
GAP_MS = 100
POST_US = POST_MS * 1000
PRE_US = PRE_MS *1000
GAP_S = GAP_MS  / 1000.0
SHORT = 10
FREQ = 38
TOLERANCE  = 15
TOLER_MIN =  (100 - TOLERANCE) / 100.0
TOLER_MAX =  (100 + TOLERANCE) / 100.0

class Remocon:
    def __init__(self) -> None:
        self.in_code = False
        self.fetching_code = False
        self.last_tick = 0
        self.code = []
        self.pi = pigpio.pi()
        self.pi.set_mode(GPIO_IN, pigpio.INPUT)
        self.pi.set_mode(GPIO_OUT, pigpio.OUTPUT)
        
        
    def __del__(self) -> None:
        self.pi.stop()
    
    def record(self,label:str):
        try:
            with open(os.path.join(FILE,label), "r") as f:
                records = json.load(f)
        except:
            records = {}
        cb = self.pi.callback(GPIO_IN, pigpio.EITHER_EDGE, self.cbf)  # type: ignore
        print("Recording")
        self.fetching_code = True
        while self.fetching_code:
            sleep(0.1)
        print("Okay")
        sleep(0.5)
        records[label] = self.code[:]
        self.tidy(records)
        with open(os.path.join(FILE,label), "w+") as f:
            f.write(json.dumps(records, sort_keys=True).replace("],", "],\n")+"\n")
        
        
        
    
    def play(self,label:str):
        records = {}
        with open(os.path.join(FILE,label),"r") as f:
            records = json.load(f)
        self.pi.wave_add_new()
        emit_time = time()
        self.code = records[label]
        marks_wid = {}
        spaces_wid = {}
        wave = [0]*len(self.code)
        
        for i in range(0, len(self.code)):
            ci = self.code[i]
            if i & 1: # Space
               if ci not in spaces_wid:
                  self.pi.wave_add_generic([pigpio.pulse(0, 0, ci)])
                  spaces_wid[ci] = self.pi.wave_create()
               wave[i] = spaces_wid[ci]
            else: # Mark
               if ci not in marks_wid:
                  wf = self.carrier(GPIO_OUT, FREQ, ci)
                  self.pi.wave_add_generic(wf)
                  marks_wid[ci] = self.pi.wave_create()
               wave[i] = marks_wid[ci]

        delay = emit_time - time()
        
        if delay > 0.0:
            sleep(delay)
        
        self.pi.wave_chain(wave)
        
        while self.pi.wave_tx_busy():
            sleep(0.002)
        emit_time = time() + GAP_S
        for i in marks_wid:
            self.pi.wave_delete(marks_wid[i])
        for i in spaces_wid:
            self.pi.wave_delete(spaces_wid[i])
        
    def carrier(self,gpio,frequency, micros):
        wf = []
        cycle = 1000.0 / frequency
        cycles = int(round(micros/cycle))
        on = int(round(cycle / 2.0))
        sofar = 0
        for c in range(cycles):
            target = int(round((c+1)*cycle))
            sofar += on
            off = target - sofar
            sofar += off
            wf.append(pigpio.pulse(1<<gpio, 0, on))
            wf.append(pigpio.pulse(0, 1<<gpio, off))
        return wf
        

    def tidy_mark_space(self,records, base):
        ms = {}
        for rec in records:
            rl = len(records[rec])
            for i in range(base, rl, 2):
                if records[rec][i] in ms:
                    ms[records[rec][i]] += 1
                else:
                    ms[records[rec][i]] = 1
        v = None
        e = []
        tot = 0
        similar = 1
        for plen in sorted(ms):
            if v == None:
                e = [plen]
                v = plen
                tot = plen * ms[plen]
                similar = ms[plen]

            elif plen < (v*TOLER_MAX):
                e.append(plen)
                tot += (plen * ms[plen])
                similar += ms[plen]
            else:
                v = int(round(tot/float(similar)))
                # set all previous to v
                for i in e:
                    ms[i] = v
                e = [plen]
                v = plen
                tot = plen * ms[plen]
                similar = ms[plen]

        v = int(round(tot/float(similar)))
        for i in e:
            ms[i] = v
        for rec in records:
            rl = len(records[rec])
            for i in range(base, rl, 2):
                records[rec][i] = ms[records[rec][i]]


    def tidy(self, records):
        self.tidy_mark_space(records, 0) # Marks.
        self.tidy_mark_space(records, 1) # Spaces.
        
    def normalise(self):
        entries = len(self.code)
        p = [0]*entries # Set all entries not processed.
        for i in range(entries):
            if not p[i]: # Not processed?
                v = self.code[i]
                tot = v
                similar = 1.0

                # Find all pulses with similar lengths to the start pulse.
                for j in range(i+2, entries, 2):
                    if not p[j]: # Unprocessed.
                        if (self.code[j]*TOLER_MIN) < v < (self.code[j]*TOLER_MAX): # Similar.
                            tot = tot + self.code[j]
                            similar += 1.0

                # Calculate the average pulse length.
                newv = round(tot / similar, 2)
                self.code[i] = newv

                # Set all similar pulses to the average value.
                for j in range(i+2, entries, 2):
                    if not p[j]: # Unprocessed.
                        if (self.code[j]*TOLER_MIN) < v < (self.code[j]*TOLER_MAX): # Similar.
                            self.code[j] = newv
                            p[j] = 1

    def end_of_code(self):
        if len(self.code) > SHORT:
            self.normalise()
            self.fetching_code = False
        else:
            self.code = []
            print("Short code, probably a repeat, try again")
    
    def cbf(self, gpio, level, tick):
        if level != pigpio.TIMEOUT:

            edge = pigpio.tickDiff(self.last_tick, tick)
            self.last_tick = tick

            if self.fetching_code:

                if (edge > PRE_US) and (not self.in_code): # Start of a code.
                    self.in_code = True
                    self.pi.set_watchdog(GPIO_IN, POST_MS) # Start watchdog.

                elif (edge > POST_US) and self.in_code: # End of a code.
                    self.in_code = False
                    self.pi.set_watchdog(GPIO_IN, 0) # Cancel watchdog.
                    self.end_of_code()

                elif self.in_code:
                    self.code.append(edge)

        else:
            self.pi.set_watchdog(GPIO_IN, 0) # Cancel watchdog.
            if self.in_code:
                self.in_code = False
                self.end_of_code()