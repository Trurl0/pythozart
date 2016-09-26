#!usr/bin/env python  
#coding=utf-8  
'''
    <Pythozart: not-so-random noise generator.>
    Copyright (C) 2015  @author: Trurl

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

'''
  TODO list:
  Change name:
	Ideas:
		Trurl's electroband
		Trurl's electrobard
		Pythovsky/Pytor Pykovsky

  Code improvements:
	Separate functions in different files for readability (careful with py2exe)
	Check functions parameters and abuse of global parameters within functions
	Organize modes and parameters, specially chords and random ones
	Don't select notes for voices not playing
	Remove extra Key note from scales (root note is repeated in order to comply with musical notation, this causes a higher probability of root in random choices within scales)
	FIX problem between different octaves (beginning in C) to comply with musical notation beginning in C FIXED, worth noting.
  
  Improve melody:
	Melodic intervals (Test: Weighted dictionary of melodic jumps, select note based on previous + weight selected jump)
	lastDissonance size check with even compassBeats (3/2?)
	note: dissonance is global, each note of each voice adds to the same variable, is this ok?
	Harmonic intervals, counterpoint
	Harmonize melody
	Preference to beats in tempo? rhythm?
	Riffs or recurrent melodies or structures (fixed beginning question + open answer, store and repeat sections)?
	
  Automated Song Progression:
	Advanced song structure (+/- Intensity, different parts, peaks and relax zones, etc)
	Change parameters based on previous section or song structure
	Adapt patterns (bass, arpeggio) to general feel
	Change duration of sections depending on feeling
	Change instruments presence (and rate) based on feel
	Prioritize certain patterns (Encourage greater melodic jumps, equally distributed notes...)
	Song Change?
		Stop some seconds and re-roll entire song after some time
	  
  Miscellaneous musical improvement:
	Add drums
	Tempo should be in bpm (1/s)
	Different chord strumming patterns (+remake chords)
	Different progression sizes
	Different instruments (violin, electric guitar, uke chords...)
	Check chords  progression/scale compatibility
	Volume adjustment (for each voice?)
	Separate mode (Ionian...) from scales
  
  Advanced options:
	Set variables
		density of notes in random patterns
		Time to automated change
		time distribution of instrument presence (relaxed->less notes...)
		Number of LastNotes for dissonanceSum
		Dissonance with key or chord in melodic mode? (seems to work with chord...)
		Dissonance limits for each voice (ACHTUNG: Dissonance value is shared for all voices)
		Custom allowed beats for melody
	Change of Key and Mode during Song
	Allow keyboard and note playing (TODO: Fix delay, assign pc keys)
	Change or select/create arpeggio patterns -> Mostly done, add different octaves.
	Prepare changes before taking effect (includes instruments, set flag that controls parameter actualization inside self.play())
'''

import os, sys
import subprocess
import time
import random
import platform
import winsound
from multiprocessing import Process, freeze_support
import threading
import Tkinter

class Pythozart:
    def __init__(self):
        if platform.system()=="Windows":
            self.onWindows=True
            self.prefix="guitar\\" #"notes\\" TODO: Use for different instruments
            self.noteSufix=""                #TODO: Use for different duration of note
        else:
            self.onWindows=False
            #self.notePrefix="guitar/"
            self.noteSufix=""
		
        #SONG PARAMETERS
        #TEMPO
        #self.beatTime=.15#classBeatTime #0.15                 #Minimum time between notes (Speed of the song)
        self.compassBeats=8                             #beats per compass
        self.songProgressionBeats=self.compassBeats       #Number of beats per progression cycle. Actualized in setChordProgression
       
	    #NOTES
        self.NOTES=["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
		
	    #CHORD PROGRESSIONS
        self.CHORDS_MAJOR=[2,2,1,2,2,2,1]
        self.CHORDS_MAJOR_7th=[2,2,1,2,2,2,1]
        self.CHORDS_MAJOR_6th=[2,3,2,2,3]
        self.CHORDS_MAJOR_9th=[2,2,1,2,2,2,1]
        self.CHORDS_NATURAL_MINOR=[2,1,2,2,1,2,2]
        self.CHORDS_MELODIC_MINOR=[2,1,2,2,2,2,1]
        self.CHORDS_HARMONIC_MINOR=[2,1,2,2,1,3,1]
		
        #NOTES SCALES
        self.MAJOR=[2,2,1,2,2,2,1]   #-->saltos de la escala
        self.NATURAL_MINOR=[2,1,2,2,1,2,2]
        self.MELODIC_MINOR=[2,1,2,2,2,2,1]
        self.HARMONIC_MINOR=[2,1,2,2,1,3,1]
        self.PENTATONIC_MAJOR=[2,2,3,2,3]
        self.PENTATONIC_MINOR=[3,2,2,3,2]
        self.PENTATONIC_NEUTRAL=[2,3,2,3,2]
        self.MAJOR_BLUES=[2,1,1,3,2,3]
        self.MINOR_BLUES=[3,2,1,1,3,2]
		
        self.LYDIAN=[2,2,2,1,2,2,1]
        self.PHRYGIAN=[1,2,2,2,1,2,2]
        self.MIXOLIDIAN=[2,2,1,2,2,1,2]
        self.DORIAN=[2,1,2,2,2,1,2]
        self.LOCRIAN=[1,2,2,1,2,2,2]

        self.WHOLE_TONE=[2, 2, 2, 2, 2, 2]
        self.CHROMATIC=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        #Arpeggio patterns (Overriden by self.createArpeggioPattern())    [[beat,chordNote,octave], ... ]
        """"self.arpeggioPatterns=([[0,0,"3"],[2,1,"3"],[4,0,"3"],[6,2,"3"]],...)
        self.bassPatterns=([[0,0,"2"],[4,0,"2"]],...)"""

		#TODO: General case
        self.voiceNote=["0","0","0","0","0","0"] #Notes in a beat for melody + five random voices
        self.userArpeggio=[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
        self.userBass=[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
        self.patternShow=["    ","root"," 5th"," 3th" ]
        self.userChords=[1,1,1,1,1,1,1,1]
        self.chordsMajorShow=[" I "," I ","ii ","iii","IV","V","vi","viiº"]
        self.chordsMinorShow=[" i "," i ","iiº","III","iv","V","VI","VII","viiº"]
        self.mode="major"
        #self.allChords=["CM","Cm","Cdim","C#M","C#m","C#dim","DM","Dm","Ddim","D#M","D#m","D#dim","EM","Em","Edim","FM","Fm","Fdim","F#M","F#m","F#dim","GM","Gm","Gdim","G#M","G#m","G#dim","AM","Am","Adim","A#M","A#m","A#dim", "BM","Bm","Bdim",]

        # Global Flags
        self.waitForChangesFlag=False
		
		#Changes Flags
        self.changeChordsFlag=False #For syncronous changeChords button
        self.changeArpeggioFlag=False #For syncronous changeChords button
        self.changeBassFlag=False #For syncronous changeChords button
        self.userSetProgressionFlag=False

		#GUI Buttons
        #self.changeKeyFlag=False #For syncronous changeKey button
        self.advancedFlag=False#Displays advanced options
        self.advancedPatternFlag=False#Displays advanced pattern options
        self.testKeyboardFlag=False#Displays keyboard
        self.melodyButtonFlag=False

		#Melodic mode parameters
        self.periodicChangeFlag=True
        self.melodicDisonanceFlag=False #Experimental melodic mode
        self.dissonanceLimit=[2.0,4.0]#Check limits
        self.dissonanceLast=[]#Initialised in self.onPlayClick, depends on beats per compass
		
        #Lyrics
        #self.writePoetry=True
        self.lyricsCount=0
        self.lineCount=0
        self.nouns=self.readWords("words\\nouns.txt")
        self.verbs=self.readWords("words\\verbs.txt")
        self.adjectives=self.readWords("words\\adjectives.txt")
        self.adverbs=self.readWords("words\\adverbs.txt")
        self.pronouns=self.readWords("words\\pronouns.txt")
        self.prepositions=self.readWords("words\\prepositions.txt")
        self.structure=[
                        "As NOUN VERB",
                        "VERB in the NOUNs",
                        "The ADJ NOUN ADV VERBs the NOUN",
                        "ADJ, ADJ NOUNs",
                        "ADV VERB a ADJ, ADJ NOUN",
                        "A NOUN is a ADJ NOUN",
                        "The NOUN is a ADJ NOUN",
                        "The NOUN VERBs like a ADJ NOUN",
                        "NOUNs VERB like ADJ NOUNs",
                        "VERB ADV like a ADJ NOUN",
                        "NOUN, NOUN, and NOUN",
                        "All NOUNs VERB ADJ, ADJ NOUNs",
                        #"Never VERB a NOUN",
                        "ADV VERB a NOUN",
                        "A NOUN, ADV VERB",
                        "NOUNs, as ADJ NOUNs",
                        "PREP the ADJ NOUN",
  
                        "Why does the NOUN VERB?",
                        "Why the ADJ NOUN?",
                        "Where is the ADJ NOUN?",
                        "When will the NOUN VERB?",
                        "What NOUN will VERB the NOUNs?",
                        "ADV a ADJ NOUN?",
                        "ADV VERB?",
                        "NOUN?",

                        "NOUNs VERB!",
                        "A ADJ NOUN!",
                        "ADV VERB!",
                        "NOUN!",
                        "A ADJ NOUN!",
                        ]

				
        #Initialize GUI
        self.createGUI()

    def initPlay(self):
        #Set song parameters
        self.beatTime=self.tempoScale.get()
        self.compassBeats=self.beatsScale.get()
        #self.songProgressionBeats=self.compassBeats
        self.autoChangeTime=self.compassBeats*8 #Automatic progression change each 16 chords, regardless of progression length to avoid actualization. TODO: make this a parameter

        #Dissonance initialization
        for i in range(self.compassBeats):#Check this or make a parameter
            self.dissonanceLast.append((self.dissonanceLimit[0]+self.dissonanceLimit[1])/2)

        #Set key
        self.key=self.guiKey.get()
        rootPos=self.NOTES.index(self.key)
        print "Key: "+self.NOTES[rootPos]

        #Notes scale  #TODO: Maybe use a dictionary here, don't you think...?
        if self.guiScale.get()=="Major":
            self.incrementalScale=self.MAJOR
        elif self.guiScale.get()=="Natural Minor":
            self.incrementalScale=self.NATURAL_MINOR
        elif self.guiScale.get()=="Harmonic Minor":
            self.incrementalScale=self.HARMONIC_MINOR
        elif self.guiScale.get()=="Melodic Minor":
            self.incrementalScale=self.MELODIC_MINOR
        elif self.guiScale.get()=="Blues Major":
            self.incrementalScale=self.MAJOR_BLUES
        elif self.guiScale.get()=="Blues Minor":
            self.incrementalScale=self.MINOR_BLUES
        elif self.guiScale.get()=="Pentatonic Major":
            self.incrementalScale=self.PENTATONIC_MAJOR
        elif self.guiScale.get()=="Pentatonic Minor":
            self.incrementalScale=self.PENTATONIC_MINOR
        elif self.guiScale.get()=="Pentatonic Neutral":
            self.incrementalScale=self.PENTATONIC_NEUTRAL
        elif self.guiScale.get()=="Lydian":
            self.incrementalScale=self.LYDIAN
        elif self.guiScale.get()=="Phrygian":
            self.incrementalScale=self.PHRYGIAN
        elif self.guiScale.get()=="Mixolidian":
            self.incrementalScale=self.MIXOLIDIAN
        elif self.guiScale.get()=="Dorian":
            self.incrementalScale=self.DORIAN
        elif self.guiScale.get()=="Locrian":
            self.incrementalScale=self.LOCRIAN
        elif self.guiScale.get()=="Whole Tone":
            self.incrementalScale=self.WHOLE_TONE
        elif self.guiScale.get()=="Chromatic":
            self.incrementalScale=self.CHROMATIC
        else:
            print "ERROR: SCALE NOT FOUND, CHOSING AT RANDOM"
            self.incrementalScale=random.choice([self.MAJOR,self.MAJOR,self.MAJOR,self.NATURAL_MINOR,self.HARMONIC_MINOR,self.MELODIC_MINOR]) #Mode of the song

        #Chord scale
        if self.guiChords.get()=="Major":
            self.chordsincrementalScale=self.MAJOR
        elif self.guiChords.get()=="Natural Minor":
            self.chordsincrementalScale=self.NATURAL_MINOR
        elif self.guiChords.get()=="Harmonic Minor":
            self.chordsincrementalScale=self.HARMONIC_MINOR
        elif self.guiChords.get()=="Melodic Minor":
            self.chordsincrementalScale=self.MELODIC_MINOR
        elif self.guiChords.get()=="Major 7th":
            self.chordsincrementalScale=self.MAJOR_7th
        else:
            self.chordsincrementalScale=random.choice([self.CHORDS_MAJOR,self.CHORDS_MAJOR,self.CHORDS_MAJOR_7th,self.CHORDS_NATURAL_MINOR,self.CHORDS_HARMONIC_MINOR,self.CHORDS_MELODIC_MINOR]) #Mode of the song

        if (self.chordsincrementalScale==self.CHORDS_MAJOR) or (self.chordsincrementalScale==self.CHORDS_MAJOR_7th):
            self.mode="major"
        else:
            self.mode="minor"

        #Arpeggios
        self.arpeggioPattern=self.createArpeggioPattern(self.compassBeats) #random.choice(self.arpeggioPatterns)
        self.bassPattern=self.createBassPattern(self.compassBeats)#random.choice(self.bassPatterns)

        #Voices
        self.voice5presence=100-((self.voice5scale.get())*.6)  #60-100
        self.voice4presence=100-((self.voice4scale.get())*.6)
        self.voice3presence=100-((self.voice3scale.get())*.6)
        self.voice2presence=100-((self.voice2scale.get())*.6)
        self.hasVoice=[self.hasChords.get(),0,self.hasVoice2.get(),self.hasVoice3.get(),self.hasVoice4.get(),self.hasVoice5.get(),self.hasArpeggio.get(),self.hasBass.get()]
        self.voiceRate=[0,0,self.voice2presence,self.voice3presence,self.voice4presence,self.voice5presence]
        
        #Generate chord list
        self.CHORDS_SCALE=self.makeScale(rootPos,self.chordsincrementalScale,self.NOTES)
        self.CHORDS=[]
        for i in range(0,len(self.CHORDS_SCALE)):
            self.CHORDS.append(self.CHORDS_SCALE[i])
        self.CHORDS=self.makeChordScale(self.CHORDS,self.guiChords.get())
        self.lastChord=self.CHORDS[0]
        print "Chords: "+self.guiChords.get()
        print self.CHORDS

        #Generate notes for each chord of the list
        self.CHORD_NOTES=self.selectNotesForChordScale(self.CHORDS)

        #Generate scale
        self.SCALE=self.makeScale(rootPos,self.incrementalScale,self.NOTES)
        print "Scale: "+self.guiScale.get()
        print self.SCALE
        print "Chord progression: "

        
        #CHORDS TODO:Purge useless chord options
        self.chordProgressionFlag=1            #Enables chords progressions (but doesn't control chords sounding)
        self.chordProgressionRandom=0
        self.chordWithMelody=0                 #Chord selected to acompany melody2
        self.chordbeatsCount=0                 #Counter for chord progressions
        self.chordProgressionCount=0           #Counter for chord progressions
        self.lastChord="0"                     #For chord progressions
        self.lastChordRandom=0                 #For chord progressions
        self.outOfChordMelodyFactor=33 #[0,0,1]  #Melody notes extraced from chord factor
        self.outOfChordBassFactor=[0]          #Bass notes extraced from chord factor
        #MELODY
        self.melodyBeatsCount=0                #For melodic mode


        #Set chord progression
        if self.chordProgressionFlag:
            self.setChordProgression(self.mode)
            self.chordProgressionCounter=0
        

        print "\nSTART PYTHOZART!"
        self.playing=True
        self.playButton.config(text="Stop", command=self.onStopClick)

        #Start playing in new thread
        self.playThread = threading.Thread(target=self.play).start()

#Main loop
    def play(self):
        #Makes music, selects notes for all instruments, plays some of them, waits for tempo and repeats
        self.beatsCount=-1    #Counts total beats in a song
        self.compassCount=-1  #Counts beats in a single compass
        #self.progressionCount=-1  #Counts beats in a single progression
        self.lastChord=self.CHORDS[self.chordProgression[len(self.chordProgression)-1]]   #Begin with root chord

        #Sound non stop
        while self.playing:
            tBeat=time.time() #Tic Toc for beat time
            #Actualize song Counters
            self.beatsCount=self.beatsCount+1
            if self.compassCount<self.compassBeats-1:
                self.compassCount=self.compassCount+1
            else:
                self.compassCount=0
            #print ""
            #print self.beatsCount
            #print self.compassCount
            #print ""

            #PERIODIC CHANGES CHECK THIS!!  when the button is not present in the GUI and NOT INITIALIZED, this test is False, although the value was initialized to False
            if not self.waitForChangesFlag:
                self.hasVoice=[self.hasChords.get(),self.hasVoice1.get(),self.hasVoice2.get(),self.hasVoice3.get(),self.hasVoice4.get(),self.hasVoice5.get(),self.hasArpeggio.get(),self.hasBass.get()]

                self.beatTime=self.tempoScale.get()
                self.voice5presence=100-((self.voice5scale.get())*.6)  #60-100
                self.voice4presence=100-((self.voice4scale.get())*.6)
                self.voice3presence=100-((self.voice3scale.get())*.6)
                self.voice2presence=100-((self.voice2scale.get())*.6)
                self.voiceRate=[0,0,self.voice2presence,self.voice3presence,self.voice4presence,self.voice5presence]
                #Select check and limits for melodic mode and force Sup>Inf+margin
                if self.melodyButtonFlag:
                    self.melodicDisonanceFlag=self.melodicDisonanceMode.get()
                    if self.dissonanceInfLimitScale.get()>self.dissonanceSupLimitScale.get():#Force Inf<Sup-1
                        self.dissonanceInfLimitScale.set(self.dissonanceSupLimitScale.get()-1.0)
                    if self.dissonanceSupLimitScale.get()<self.dissonanceInfLimitScale.get():#Force Sup>Inf+1
                        self.dissonanceSupLimitScale.set(self.dissonanceInfLimitScale.get()+1.0)
                    self.dissonanceLimit[0]=self.dissonanceInfLimitScale.get()
                    self.dissonanceLimit[1]=self.dissonanceSupLimitScale.get()
                if not self.melodicDisonanceFlag:
                    self.outOfChordMelodyFactor=self.outOfChordScale.get()
                self.periodicChangeFlag=self.periodicChangeMode.get()


                #On demand Chord progression change
                if (self.changeChordsFlag) and (self.chordProgressionCounter==0) and (self.compassCount==0):
                    self.changeChordsFlag=False
                    print "\nChord progression changed\n"
                    self.setChordProgression(self.mode)
                #On demand Chord progression change
                if (self.userSetProgressionFlag) and (self.chordProgressionCounter==0) and (self.compassCount==0):
                    self.userSetProgressionFlag=False
                    print "\nUser progression set\n"
                    self.chordProgression=list(self.userChords)
                    print self.chordProgression
                #On demand Arpeggio change
                if (self.changeArpeggioFlag):# Immediate effect
                    self.changeArpeggioFlag=False
                    print "\nArpeggio pattern changed\n"
                    self.arpeggioPattern=self.createArpeggioPattern(self.compassBeats)
                #On demand Bass change
                if (self.changeBassFlag):# Immediate effect
                    self.changeBassFlag=False
                    print "\nBass pattern changed\n"
                    self.bassPattern=self.createBassPattern(self.compassBeats)
                #Periodic change
                if (self.periodicChangeFlag)and(self.beatsCount>self.autoChangeTime) and (self.chordProgressionCounter==0) and (self.compassCount==0):
                    self.setChordProgression(self.mode)
                    self.arpeggioPattern=self.createArpeggioPattern(self.compassBeats)
                    self.bassPattern=self.createBassPattern(self.compassBeats)
                    self.beatsCount=0
                    self.setRandomParameters()
                    #print "PERIODIC CHANGE"


            #NOTES AND CHORDS SELECTION
            #Select chord
            if self.chordProgressionFlag!=0:
                self.chordNote=self.selectChordFromProgression(self.compassCount, self.CHORDS)
            elif self.chordProgressionRandom!=0:
                self.chordNote=self.selectChordFromProgressionRandom(self.compassBeats, self.CHORDS)
            else:
                self.chordNote=self.selectNoteRandom(self.CHORDS, self.voiceRate[0])
            if self.chordNote !="0":
                self.lastChord=self.chordNote

            #Select arpeggio notes
            self.arpeggioNote="0"
            if self.hasVoice[6]!=0:
                self.arpeggioNote=self.selectArpeggioNote(self.lastChord,self.compassCount,self.arpeggioPattern)
    
            #Select bass arpeggio notes
            self.bassNote="0"
            if self.hasVoice[7]!=0:
                self.bassNote=self.selectArpeggioNote(self.lastChord,self.compassCount,self.bassPattern)
    

            #Select notes #Maybe this should be a separate function...
            #if self.chordProgressionFlag!=0:#Remove this parameter...

            #Melody
            if self.hasVoice[1]!=0:
                if not self.compassCount:
                    #phrase=self.createPhrase(self.SCALE, self.lastChord, 0, self.compassBeats)
                    phrase, phrasePos =self.createPhrase2(self.SCALE, self.lastChord, 0, self.compassBeats)# Trying new phrases
                    #print phrase
                #print "PHRASE: "+str(phrase[self.compassCount])
                if not self.writePoetry.get():
                    try:
                        print " "*(phrasePos[self.compassCount])+str(phrase[self.compassCount])
                    except:
                        pass
                #BUG PHRASE referenced before assignment
                try:
                    if phrase[self.compassCount] !="0":
                        self.voiceNote[1] = phrase[self.compassCount]
                    else:
                        self.voiceNote[1] = "01"
                except:
                    print "\nphrase referenced before assignment error, assigning"
                    phrase, phrasePos =self.createPhrase2(self.SCALE, self.lastChord, 0, self.compassBeats)# Trying new phrases
                    if phrase[self.compassCount] !="0":
                        self.voiceNote[1] = phrase[self.compassCount]
                    else:
                        self.voiceNote[1] = "01"
                #BUG PHRASE referenced before assignment


            #Chord+random notes
            rand=random.randint(0,100)
            if rand>self.outOfChordMelodyFactor:
                for i in range(3,6):
                    #self.voiceNote[i]="0" #Init for voices not playing (not necesary here, doesn't hurt either)
                    #if self.hasVoice[i]!=0:
                    self.voiceNote[i]= self.selectNoteFromChord(self.lastChord, self.voiceRate[i])+str(i)
            else:
                for i in range(3,6):
                    #self.voiceNote[i]="0" #Init for voices not playing (not necesary here, doesn't hurt either)
                    #if self.hasVoice[i]!=0:
                    self.voiceNote[i]= self.selectNoteRandom(self.SCALE, self.voiceRate[i])+str(i)
            #Bass notes always from chords:
            self.voiceNote[2]= self.selectNoteFromChord(self.lastChord, self.voiceRate[2])+"2"


            #Play all
            if self.arpeggioNote !="0" and self.hasVoice[6]!=0:
                self.playNote(self.arpeggioNote+self.noteSufix)
            if self.bassNote !="0" and self.hasVoice[7]!=0:
                self.playNote(self.bassNote+self.noteSufix)
            for i in range(1,6):
                if self.voiceNote[i] !="0"+str(i) and self.hasVoice[i]!=0:
                    self.playNote(self.voiceNote[i]+self.noteSufix)
            if self.chordNote !="0":        
                if self.hasVoice[0]!=0:
                    self.playChord(self.chordNote)
    
    
            #Lyrics
            if not self.compassCount: #Generate a verse each compass
                verse = self.verse()
                if not self.lyricsCount: #Print a space after 4th verse
                    self.lyricsCount = 4
                    if self.writePoetry.get():
                        print
                self.lyricsCount -= 1
                self.lineCount = 0 # Mark begin of line for each new verse (to print letter by letter)
                if self.writePoetry:
                    print


            while time.time()-tBeat<self.beatTime: # Wait until tBeat has passed
                if self.lineCount < len(verse):
                    if self.writePoetry.get():
                        sys.stdout.write(verse[self.lineCount])
                    self.lineCount+=1
                    time.sleep(self.beatTime/10)

####################<MUSIC>####################
#Create structures
    def makeScale(self,rootPos,rawscale,notes):
            #Creates a scale based on relative scales
            numscale=[]
            note=0
            scale=[self.NOTES[rootPos]]
            for i in rawscale:
                numscale.append(note)
                note = note+i
            for i in range(0,len(numscale)):
                numscale[i]=numscale[i]+rootPos
                if numscale[i]>11:
                    numscale[i]=numscale[i]-12
                scale.append(self.NOTES[numscale[i]])
            return scale
        
    def makeChordScale(self,scale,mode):
        #Creates a Chord scale based on relative scales
        chordScale=scale
        if mode in ["Major","Major 7h"]:
            for i in range(0,len(scale)):
                if i in [2,3,6]:
                    chordScale[i]=chordScale[i]+"m"
                elif i in [7]:
                    chordScale[i]=chordScale[i]+"dim"
                else:
                    chordScale[i]=chordScale[i]+"M"
        elif mode in ["Natural Minor"]:
            chordScale.append(chordScale[7]) # TODO: CHECK THIS APPEND! (in setChordProgression)
            for i in range(0,len(scale)):
                if i in [0,1,4,5]:
                    chordScale[i]=chordScale[i]+"m"
                elif i in [2,8]:
                    chordScale[i]=chordScale[i]+"dim"
                else:
                    chordScale[i]=chordScale[i]+"M"
        elif mode in ["Melodic Minor"]:
            chordScale.append(chordScale[7])
            for i in range(0,len(scale)):
                if i in [0,1,2]:
                    chordScale[i]=chordScale[i]+"m"
                elif i in [2]:
                    chordScale[i]=chordScale[i]+"dim"
                else:
                    chordScale[i]=chordScale[i]+"M"
        elif mode in ["Harmonic Minor"]:
            chordScale.append(chordScale[7])
            for i in range(0,len(scale)):
                if i in [0,1,2,4]:
                    chordScale[i]=chordScale[i]+"m"
                elif i in [2,7]:
                    chordScale[i]=chordScale[i]+"dim"
                else:
                    chordScale[i]=chordScale[i]+"M"
        return chordScale

    def selectNotesForChordScale(self,chordScale):
        #Select Notes for each chord of a scale
        CHORD_NOTES=[]
        for i in range(1,len(chordScale)):
            if self.CHORDS[i][1]=="#":
                mode=self.CHORDS[i][2]
                rootPos=self.NOTES.index(self.CHORDS[i][0]+self.CHORDS[i][1]) #Checks for "NOTE"+"#"
            else:
                mode=self.CHORDS[i][1]
                rootPos=self.NOTES.index(self.CHORDS[i][0])
            CHORD_NOTES.append(self.selectNotesForChord(rootPos,mode))
        return CHORD_NOTES

    def selectNotesForChord(self,rootPos,mode):
        #Select Notes for a chord given by its root note and its mode
        CHORD_SCALE=[]
        if mode=="m":
            CHORD_NOTES=[0,3,7]
        elif mode=="d":
            CHORD_NOTES=[0,3,6]
        else:#"M"
            CHORD_NOTES=[0,4,7]
        for i in range(0,len(CHORD_NOTES)):
            CHORD_NOTES[i]=CHORD_NOTES[i]+rootPos #Get index in NOTES with offset in rootPos
            if CHORD_NOTES[i]>11:
                CHORD_NOTES[i]=CHORD_NOTES[i]-12
            CHORD_SCALE.append(self.NOTES[CHORD_NOTES[i]])
        return CHORD_SCALE

    def setChordProgression(self,mode):
		#Creates a chord progression from the chord scale.
        self.progressionSize=random.choice([4,8])#TODO: Create this depending on beats
        self.songProgressionBeats=self.compassBeats*self.progressionSize
        if mode!="minor":
            for i in range(0,self.progressionSize):
                if i==0:
                    self.chordProgression=[1]#Begin with root
                elif self.chordProgression[i-1]==1:
                    self.chordProgression.append(random.choice([5,5,5,5,7]))
                elif self.chordProgression[i-1]==2:
                    self.chordProgression.append(random.choice([1,6]))
                elif self.chordProgression[i-1]==3:
                    self.chordProgression.append(random.choice([1,1,7]))
                elif self.chordProgression[i-1]==4:
                    self.chordProgression.append(random.choice([1,6]))
                elif self.chordProgression[i-1]==5:
                    self.chordProgression.append(random.choice([1,2,4]))
                elif self.chordProgression[i-1]==6:
                    self.chordProgression.append(random.choice([1,3]))
                elif self.chordProgression[i-1]==7:
                    self.chordProgression.append(random.choice([1,2,4]))
        else:
            for i in range(0,self.progressionSize):
                if i==0:
                    self.chordProgression=[1]#Begin with root
                elif self.chordProgression[i-1]==1:
                    self.chordProgression.append(random.choice([5,5,5,5,5,5]))
                elif self.chordProgression[i-1]==2:
                    self.chordProgression.append(random.choice([1,6]))
                elif self.chordProgression[i-1]==3:
                    self.chordProgression.append(random.choice([1,7]))
                elif self.chordProgression[i-1]==4:
                    self.chordProgression.append(random.choice([1,6]))
                elif self.chordProgression[i-1]==5:
                    self.chordProgression.append(random.choice([1,1,2,4,4]))
                elif self.chordProgression[i-1]==6:
                    self.chordProgression.append(random.choice([1,3]))
                elif self.chordProgression[i-1]==7:
                    self.chordProgression.append(random.choice([1,1,4]))
                elif self.chordProgression[i-1]==8:
                    self.chordProgression.append(random.choice([1,1,2,4,4]))
        self.chordProgression.reverse()
        print
        print self.chordProgression 
        return self.chordProgression
    
    def createArpeggioPattern(self,compassBeats):
        pattern=[]
        for i in range(0,compassBeats,2):# Only even beats
            if random.choice([0,1,1])==1:
                pattern.append([i,random.choice([0,1,2]),random.choice(["3","3","4"])]) #More notes from 3th octave...
        return pattern

    def createBassPattern(self,compassBeats):
        pattern=[]
        for i in range(0,compassBeats,2):# Only even beats
            if i==0:
                pattern.append([i,0,"2"]) #Always play root note
            elif random.choice([0,0,1])==1:
                pattern.append([i,random.choice([0,0,1,2]),"2"]) #All notes from 2th octave, more root
        return pattern	
    
    def setRandomParameters(self):
        #self.tempoScale.set(self.tempoScale.get()+random.uniform(-0.01,+0.01)) #Only small tempo variations?
        if random.choice([1,1,1]):#Chords, never
            self.chordsCheck.deselect()
        else:
            self.chordsCheck.select()
	
        if random.choice([0,0,0,1]):#Arpeggio
            self.arpeggioCheck.deselect()
        else:
            self.arpeggioCheck.select()
        if random.choice([0,1]):#Bass
            self.bassCheck.deselect()
        else:
            self.bassCheck.select()
			
        if random.choice([0,0,1]):#Melody
            self.voice1Check.deselect()		
            if random.choice([0,0,1]):#Bass
                self.bassCheck.deselect()
            else:
                self.bassCheck.select()	
            if random.choice([0,1]):#Voice5
                self.voice5Check.deselect()
            else:
                self.voice5Check.select()
            if random.choice([0,0,1]):#Voice4
                self.voice4Check.deselect()
            else:
                self.voice4Check.select()
            if random.choice([0,1]):#Voice3
                self.voice3Check.deselect()
            else:
                self.voice3Check.select()
            if random.choice([0,1,1,1]):#Voice2
                self.voice2Check.deselect()
            else:
                self.voice2Check.select()
        else:
            self.voice1Check.select()
			
            if random.choice([0,1,1]):#Voice5
                self.voice5Check.deselect()
            else:
                self.voice5Check.select()
            if random.choice([0,1,1,1]):#Voice4
                self.voice4Check.deselect()
            else:
                self.voice4Check.select()
            if random.choice([0,1,1,1,1]):#Voice3
                self.voice3Check.deselect()
            else:
                self.voice3Check.select()
            if random.choice([1,1,1]):#Voice2, never with melody
                self.voice2Check.deselect()
            else:
                self.voice2Check.select()

			
        self.voice5scale.set(random.randint(20,60))
        self.voice4scale.set(random.randint(20,60))
        self.voice3scale.set(random.randint(10,50))
        self.voice2scale.set(random.randint(10,50))
		
        self.beatsCount=0
           
#Select notes 
    def selectNoteRandom(self, scale, rate):
        #Select a silence or a note from the scale
        note="0"
        rand=random.randint(0,100)
        if  rand >rate:
            note=random.choice(scale)
        return note

    def selectNoteFromChord(self, chord, rate):
        #Select a silence or a note from a chord
        note="0"
        rand=random.randint(0,100)
        if  rand >rate:
            notePos=self.CHORDS.index(chord)
            if notePos!=0:
                notePos=notePos-1
            note=random.choice(self.CHORD_NOTES[notePos])
        return note
 
    def selectNoteDisonance(self, scale, chord, rate, beats):
		#Selects a note based on melodic dissonance, accumulated in the last notes (using self.compassCount, irrelevant?)
        note="0"
        rand=random.randint(0,100)
        if rand>rate:
            note=random.choice(scale)#Choose new note
			
			#Get relative positions
            if not self.CHORDS.index(chord):
                chordRoot=self.CHORD_NOTES[self.CHORDS.index(chord)][0]
            else:
                chordRoot=self.CHORD_NOTES[self.CHORDS.index(chord)-1][0]
            notePos=self.NOTES.index(note)
            chordRootPos=self.NOTES.index(chordRoot)
            rootPos=self.NOTES.index(self.CHORD_NOTES[0][0])

			
	    	#Get dissonance
            dissonance=self.dissonance(notePos, chordRootPos)# or rootPos
            self.dissonanceLast.pop(0)#Remove oldest
            self.dissonanceLast.append(dissonance)#Add new
            #print "DissonanceLast: "+str(self.dissonanceLast)
            print "DissonanceSum: "+str(sum(self.dissonanceLast)/(self.compassBeats))

            whileCount=0
            while not (self.dissonanceLimit[0]< (sum(self.dissonanceLast)/(self.compassBeats)) <self.dissonanceLimit[1]):
                note=random.choice(scale)#Choose new note
                notePos=self.NOTES.index(note)#Get pose
                dissonance=self.dissonance(notePos, chordRootPos)#Get dissonance
                self.dissonanceLast.pop(0)#Remove older
                self.dissonanceLast.append(dissonance)#Add new
                whileCount=whileCount+1
                if whileCount>50:
                    print "Exceeded Dissonance Limits!"
                    break
                #print "**********Dissonance exceeded*********"
                #print "DissonanceLast: "+str(self.dissonanceLast)
                #print "DissonanceSum: "+str(sum(self.dissonanceLast)/self.compassBeats)
        return note
		
    def createPhrase(self, scaleIn, chord, rate, compassBeats):
		#Creates a phrase (list of notes) for a compass, following Nina's guidance
        phraseNotes=[]
        phraseNotesPos=[]
        phraseJumps=[]
        scale = scaleIn[:]#Pass by value TODO: Remove extra root to avoid this
        scale.pop(0)#Remove repeated root from scale
        octave=4		

		#Pick first note from chord
        note=self.selectNoteFromChord(chord,0)#Choose first note at random from chord
		#Override with chordRoot
        #if not self.CHORDS.index(chord):
        #    note=self.CHORD_NOTES[self.CHORDS.index(chord)][0]
        #else:
        #    note=self.CHORD_NOTES[self.CHORDS.index(chord)-1][0]
	
		#Get position in scale
        try:
            notePos=scale.index(note)#Get position of first note in scale
        except:#Watch for out-of scale chord notes, and pick root
            if not self.CHORDS.index(chord):
                note=self.CHORD_NOTES[self.CHORDS.index(chord)][0]
            else:
                note=self.CHORD_NOTES[self.CHORDS.index(chord)-1][0]
            try:
                notePos=scale.index(note)
            except:
                notePos=0#If chord note is not in scale pick root and continue anyway.
                print "CHORD NOT IN SCALE!"				
        phraseNotes.append(note+str(octave))#Append first note
        phraseNotesPos.append(notePos) #Choose first notePos
		
		#Pick the rest via in-scale jumps
        jumpSum=0
        jump=0
        phraseLength=random.randint(int(compassBeats*0.5),compassBeats-1)#Select length of the phrase
        #print "PhraseLength: "+str(phraseLength)
        for i in range(1,compassBeats):
            if i < phraseLength:
				#<Criteria for next note selection>
                if -5<jumpSum<5:#Check sum of last jumps limits, get down if going too high or low
                    if -3<jump<3:#Check last jump limits
                        #if jumpSum!=0:#Check if we have just corrected a limit break
                            if jump>0:#Check last jump and keep with the flow
                                jump=random.choice([3,2,1,1,1,1,1,0,-1,-2,-3])
                            else:
                                jump=random.choice([3,2,1,0,-1,-1,-1,-1,-1,-2,-3])
                        #else:#If we have just corrected a jump, go wherever?s
                            #jump=random.choice([3,2,1,1,1,0,-1,-1,-1,-2,-3])
                    else:
                        if jump>0:
                            jump=-1
                        else:
                            jump=1
                        jumpSum=0
                        #print "jumpSum RESET"
                else:
                    if jumpSum>0:
                        jump=-1
                    else:
                        jump=1
                    jumpSum=0
                    #print "jumpSum RESET"
				#</Criteria for next note selection>
    

                jumpSum=jumpSum+jump
                notePos=notePos+jump	
                #print "JumpSum["+str(i)+"]: "+str(jumpSum)
				
				#Check octave limits
                if notePos>len(scale)-1:
                    notePos = notePos-len(scale)
                    octave = octave+1
                if notePos<0:
                    notePos = notePos+len(scale)
                    octave = octave-1

            else:#Out of phraseLength
                notePos=""
                jump=""
				
			#Create note for list
            try:
                note=scale[notePos]+str(octave) #Get note name from position in scale
            except:
                note="0"
            rand=random.choice([0,0,1])
            if rand:
                note="0"

            phraseNotes.append(note) #Choose first note from chord
            phraseNotesPos.append(notePos) #Choose first note from chord
            phraseJumps.append(jump) #Choose first note from chord

        #print scale
        #print phraseNotesPos
        #print phraseJumps
        return phraseNotes
		
    def createPhrase2(self, scaleIn, chord, rate, compassBeats):
	    #TODO: Pass as parameter: jump choice, note presence, phrase length
		#Creates a phrase (list of notes) for a compass, following Nina's guidance
        phraseNotes=[]
        phraseNotesPos=[]
        phraseJumps=[]
        scale = scaleIn[:]#Pass by value TODO: Remove extra root to avoid this
        scale.pop(0)#Remove repeated root from scale
        octave=4

		#Pick first note from chord
        note=self.selectNoteFromChord(chord,0)#Choose first note at random from chord

		#Get position in scale
        try:
            notePos=scale.index(note)#Get position of first note in scale
        except:#Watch for out-of scale chord notes, and pick root
            if not self.CHORDS.index(chord):
                note=self.CHORD_NOTES[self.CHORDS.index(chord)][0]
            else:
                note=self.CHORD_NOTES[self.CHORDS.index(chord)-1][0]
            try:
                notePos=scale.index(note)
            except:
                notePos=0#If chord note is not in scale pick root and continue anyway.
                print "CHORD NOT IN SCALE!"				
        phraseNotes.append(note+str(octave))#Append first note
        phraseNotesPos.append(notePos) #Choose first notePos
		
		#Pick the rest via in-scale jumps
        jumpSum=0
        jump=0
        phraseLength=random.randint(int(compassBeats*0.5),compassBeats-1)#Select length of the phrase
        #print "PhraseLength: "+str(phraseLength)
        for i in range(1,compassBeats):
            if i < phraseLength:
				#<Criteria for next note selection>
                if -5<jumpSum<5:#Check sum of last jumps limits, get down if going too high or low
                    if -3<jump<3:#Check last jump limits
                        #if jumpSum!=0:#Check if we have just corrected a limit break
                            if jump>0:#Check last jump and keep with the flow
                                jump=random.choice([3,2,1,1,1,1,1,0,-1,-2,-3])
                            else:
                                jump=random.choice([3,2,1,0,-1,-1,-1,-1,-1,-2,-3])
                        #else:#If we have just corrected a jump, go wherever?s
                            #jump=random.choice([3,2,1,1,1,0,-1,-1,-1,-2,-3])
                    else:
                        if jump>0:
                            jump=-1
                        else:
                            jump=1
                        jumpSum=0
                        #print "jumpSum RESET"
                else:
                    if jumpSum>0:
                        jump=-1
                    else:
                        jump=1
                    jumpSum=0
                    #print "jumpSum RESET"
				#</Criteria for next note selection>
    

                jumpSum=jumpSum+jump
                notePos=notePos+jump	
                #print "JumpSum["+str(i)+"]: "+str(jumpSum)
				
				#Check octave limits
                if notePos>len(scale)-1:
                    notePos = notePos-len(scale)
                    octave = octave+1
                if notePos<0:
                    notePos = notePos+len(scale)
                    octave = octave-1

            else:#Out of phraseLength
                notePos=""
                jump=""
				
			#Create note for list
            try:
                note=scale[notePos]+str(octave) #Get note name from position in scale
            except:
                note="0"
            rand=random.choice([0,0,1])
            if rand:
                note="0"

            phraseNotes.append(note)
            phraseNotesPos.append(notePos)
            phraseJumps.append(jump)

        #print scale
        #print phraseNotesPos
        #print phraseJumps
        return phraseNotes, phraseNotesPos

    def dissonance(self, lastNotePos, rootPos):
		#Calculates dissonance between two notes
		#Distance between notes
        distance=lastNotePos-rootPos
        if distance<0:
            distance=lastNotePos+12-rootPos 
        #print"Distance: "+str(distance)
		
		#dissonance= log2(lcm(A,B)) lcm=least common multiple, A,B=frequency ratio
		#http://music.stackexchange.com/questions/4439/is-there-a-way-to-measure-the-consonance-or-dissonance-of-a-chord
        if not distance:#perfect unison/octave
             dissonance=0#1 for octave
        elif  distance==1:#m2
             dissonance=7.90689 
        elif  distance==2: #M2
             dissonance=6.16993
        elif  distance==3:#m3
             dissonance=4.90689
        elif  distance==4:#M3
             dissonance=4.32193
        elif  distance==5:#P4
             dissonance=3.58496
        elif  distance==6:#A4
             dissonance=7.67243
        elif  distance==7:#P5
             dissonance=2.58496
        elif  distance==8:#m6
             dissonance=5.32193
        elif  distance==9:#M6
             dissonance=3.90689
        elif  distance==10:#m7
             dissonance=7.16993
        elif  distance==11:#M7
             dissonance=6.90689
        else:
             dissonance=10000
        return dissonance
 
    def selectChordFromProgression(self,compassCount,CHORDS_SCALE):
        #Selects a chord from a chord scale
        #TODO: Separate chord selection from time verification (self.chordbeatsCount does the same as self.compassCount)
        CHORDS=CHORDS_SCALE
        #print "self.chordbeatsCount: "+str(self.chordbeatsCount)
        if compassCount in [-1]:# vector indicating when to play chord e.g.:[2,4,6], not 0
            chord=CHORDS[self.chordProgression[self.chordProgressionCounter]]
        elif compassCount ==0:
            if self.chordProgressionCounter<len(self.chordProgression)-1:
                self.chordProgressionCounter=self.chordProgressionCounter+1
            else:
                self.chordProgressionCounter=0
            chord=CHORDS[self.chordProgression[self.chordProgressionCounter]]
            #print "\n**********\n"+str(chord)+"\n**********\n"

        else:
            chord="0"
        return chord
    
    def selectChordFromProgressionRandom(self,beats,CHORDS_SCALE):
        #TODO: Remove...
        CHORDS=CHORDS_SCALE
        if self.chordbeatsCount>beats-2:
            self.chordbeatsCount=0
            if self.lastChordRandom==0:
                chord= self.CHORDS[1]#Begin with root
                self.lastChordRandom=1
            elif self.lastChordRandom==1:
                self.lastChordRandom=random.randint(2,7)
            elif self.lastChordRandom==2:
                self.lastChordRandom=random.choice([5,5,5,5,7])
            elif self.lastChordRandom==3:
                self.lastChordRandom=6
            elif self.lastChordRandom==4:
                self.lastChordRandom=random.choice([5,5,5,5,7])
            elif self.lastChordRandom==5:
                self.lastChordRandom=1
            elif self.lastChordRandom==6:
                self.lastChordRandom=random.choice([2,4])
            elif self.lastChordRandom==7:
                self.lastChordRandom=random.choice([1,3])
            else:
                self.lastChordRandom= 1
            chord=self.CHORDS[self.lastChordRandom]
            print "\n**********\n"+str(chord)+"\n**********\n"
        else:
            self.chordbeatsCount=self.chordbeatsCount+1
            chord="0"
        return chord
    
    def selectChordFromNote(self, note, beats):
        #Harmonizes a note
        if note=="0":
            pass    

    def selectArpeggioNote(self,chord,beat,pattern):
        #Pattern=[ [beat,note,octave], ... ]
        note="0"
        #Find Chord
        if chord!="0":
            chordPos=self.CHORDS.index(chord)
            if chordPos!=0:#Fix scales...
               chordPos=chordPos-1
    
            #If in beat pointed by pattern play a note of the chord
            for i in range (0,len(pattern)):
                if beat==pattern[i][0]:
                    note=self.CHORD_NOTES[chordPos][pattern[i][1]]+str(pattern[i][2])
        return note
    
#Play sounds
    def playChord(self,chord):
        """
        note="0"
        #Find Chord
        if chord!="0":
            chordPos=self.CHORDS.index(chord)
            if chordPos!=0:#Fix scales repeating root note...
               chordPos=chordPos-1
            #If in beat pointed by pattern play a note of the chord
            for i in range (0,len(self.CHORD_NOTES[chordPos])):
                    note=self.CHORD_NOTES[chordPos][i]+"3" #All in 3th octave...
                    self.playNote(note)
        return 0
        """
        if self.onWindows:
            #print chord
            chord="chords\\"+chord
            #A = subprocess.Popen(["python", "playnoteWin.py", chord])
            Process(target=winPlay, args=(chord,)).start()
        else:
            A = subprocess.Popen(['aplay', "chords/"+ note +".wav"])

    def playNote(self,note):
        if self.onWindows:
            #print note
            note=self.prefix+note
            Process(target=winPlay, args=(note,)).start()
            #A = subprocess.Popen(["python", "playnoteWin.py", note])
            #threading.Thread(target=self.winPlay, args=(note,)).start()
        else:
            A = subprocess.Popen(['aplay', self.prefix + note +".wav"])

####################</MUSIC>####################

####################<LYRICS>####################
    def readWords(self, fileName):
        list = open(fileName).readlines()
        list=[x.strip("\n").strip(" ").strip("	") for x in list]
        return list
    def cap(self, word):
        return word.capitalize()
    def noun(self):
        return random.choice(self.nouns)
    def pronoun(self):
        return random.choice(self.pronouns)
    def verb(self):
        return random.choice(self.verbs)
    def adverb(self):
        return random.choice(self.adverbs)
    def adjective(self):
        return random.choice(self.adjectives)
    def preposition(self):
        return random.choice(self.prepositions)
    def phraseStructure(self):
        #Random choice to begin with
        return random.choice(self.structure)
    def verse(self):
        phrase = self.phraseStructure()
        verse=""
        for word in phrase.split(" "):
        
            #Replace NOUNs before NOUN!!
            if "NOUNs" in word:
                nounTemp = self.noun()+"CHECK_END" #Check if noun ends with 's' or 'y'
                if "sCHECK_END" in nounTemp or "shCHECK_END" in nounTemp or "chCHECK_END" in nounTemp:
                    nounTemp=nounTemp.replace("CHECK_END","")
                    word=word.replace("NOUNs", nounTemp+"es")
                elif "yCHECK_END" in nounTemp:
                    nounTemp=nounTemp.replace("yCHECK_END","i")
                    word=word.replace("NOUNs", nounTemp+"es")
                else:
                    nounTemp=nounTemp.replace("CHECK_END","")
                    word=word.replace("NOUNs", nounTemp+"s")
        
            word=word.replace("NOUN", self.noun())
            word=word.replace("NOUNs", self.noun()+"s")
            word=word.replace("ADJ", self.adjective())
            word=word.replace("VERB", self.verb())
            word=word.replace("ADV", self.adverb())
            word=word.replace("PREP", self.preposition())
            
            verse=verse+word+" "
            
        for vowel in ["a","e","i","o","u"]:
            verse=verse.replace(" a "+vowel," an "+vowel) #Probably some more grammatical checks are needed...
            verse=verse.replace("A "+vowel,"An "+vowel)
        return self.cap(verse)
####################</LYRICS>####################

####################<GUI>####################
    def createGUI(self):
        root=Tkinter.Tk()
        root.iconbitmap(default='pythozart.ico')
        root.resizable(False,False)
        root.title("Pythozart 0.19")

        #bgColor="light steel blue"
        #bgColor="light cyan3"
        #bgColor="snow3"
        #bgColor="#a8c4d9"
        bgColor="light steel blue"
        #fgColor="midnight blue"
        fgColor="navy blue"
		
    
        #Title and format
        title = Tkinter.Label(root, text=" Pythozart ", fg=fgColor, bg=bgColor, font=("Arial", 16), bd=5)
        #title.grid(row=0,column=3,sticky="w")
        subtitle = Tkinter.Label(root, text="(not-so-random noise generator)", fg=fgColor, font=("Arial", 8), bd=5)
        #subtitle.place(relx=0.82, rely=0.065, anchor=Tkinter.CENTER)
        subtitle.place(relx=0.5, rely=0.1, anchor=Tkinter.CENTER)
        title.place(relx=0.5, rely=0.06, anchor=Tkinter.CENTER)
        topSpace = Tkinter.Label(root, text="\n\n\n\n", anchor=Tkinter.W)
        topSpace.grid(row=0, column=0,sticky="w")
        leftSpace = Tkinter.Label(root, text="       ")
        leftSpace.grid(row=0, column=0)
        rightSpace = Tkinter.Label(root, text="       ")
        rightSpace.grid(row=1, column=4)
        space = Tkinter.Label(root, text="    \n")
        space.grid(row=5, column=0)
        space = Tkinter.Label(root, text="    \n",font=("Arial",5))
        space.grid(row=19, column=0)
        space = Tkinter.Label(root, text="    \n",font=("Arial",5))
        space.grid(row=21, column=0)
		
        #space5 = Tkinter.Label(root, text="\n", font=("Arial",1))#Tiny space
        #space5.grid(row=rowNumber-3, column=0)
        #space6 = Tkinter.Label(root, text="\n", font=("Arial",14))#Tiny space
        #space6.grid(row=rowNumber-2, column=0)
    
        #Song parameters
        #Key
        keyText = Tkinter.Label(root, text="Key:  ", font=("Arial", 10), fg=fgColor)
        keyText.grid(row=1, column=1, sticky="w")
        self.guiKey= Tkinter.StringVar()
        self.guiKey.set("C")
        keyMenu= Tkinter.OptionMenu(root, self.guiKey,"A","A#","B","C","C#","D","D#","E","F","F#","G","G#")
        keyMenu.config(width=3,fg=fgColor,bg=bgColor)
        keyMenu.grid(row=1,column=2, sticky= "w")
        #CHORD SCALE
        chordText = Tkinter.Label(root, text="Chords:  ", font=("Arial", 10), fg=fgColor)
        chordText.grid(row=2, column=1, sticky="w")
        self.guiChords= Tkinter.StringVar()
        self.guiChords.set("Major")
        chordMenu= Tkinter.OptionMenu(root, self.guiChords, "Major", "Natural Minor", "Melodic Minor","Harmonic Minor") #Major 7th, 6th and 9th
        chordMenu.config(width=13,fg=fgColor,bg=bgColor)
        chordMenu.grid(row=2,column=2, sticky= "w")
        #NOTES SCALE
        scaleText = Tkinter.Label(root, text="Scale:  ", font=("Arial", 10), fg=fgColor)
        scaleText.grid(row=3, column=1, sticky="w")
        self.guiScale= Tkinter.StringVar()
        self.guiScale.set("Major")
        scaleMenu= Tkinter.OptionMenu(root, self.guiScale, "Major", "Natural Minor", "Melodic Minor","Harmonic Minor",
        "Blues Major", "Blues Minor","Pentatonic Major","Pentatonic Minor","Pentatonic Neutral",
        "Lydian","Phrygian","Mixolidian","Dorian","Locrian", "Whole Tone","Chromatic")
        scaleMenu.config(width=13,fg=fgColor,bg=bgColor)
        scaleMenu.grid(row=3,column=2, sticky= "w")
        #Tempo
        tempoText = Tkinter.Label(root, text="       Tempo:  \n          (s)\n", font=("Arial", 10), fg=fgColor)
        tempoText.grid(row=4, column=3, sticky="nw")
        self.tempoScale = Tkinter.Scale(root, fg=fgColor,bg=bgColor, from_=0.1, to=0.5, resolution=0.01, orient=Tkinter.HORIZONTAL, length=118)
        self.tempoScale.grid(row=4, column=3, sticky="ne")
        self.tempoScale.set(0.28)
        #Beats
        beatsText = Tkinter.Label(root, text="Beats\n /Bar:", font=("Arial", 10), fg=fgColor)
        beatsText.grid(row=4, column=1, sticky="nw")
        self.beatsScale = Tkinter.Scale(root, fg=fgColor,bg=bgColor, from_=1, to=16, resolution=1, orient=Tkinter.HORIZONTAL, length=118)
        self.beatsScale.grid(row=4, column=2, sticky="nw")
        self.beatsScale.set(12)

        #Voices
        voicesText = Tkinter.Label(root, text="Voices:  ", font=("Arial", 10), fg=fgColor)
        voicesText.grid(row=11, column=1)
    
        self.hasChords=Tkinter.IntVar()
        self.hasArpeggio=Tkinter.IntVar()
        self.hasBass=Tkinter.IntVar()
        self.hasVoice1=Tkinter.IntVar()
        self.hasVoice5=Tkinter.IntVar()
        self.hasVoice4=Tkinter.IntVar()
        self.hasVoice3=Tkinter.IntVar()
        self.hasVoice2=Tkinter.IntVar()
        self.chordsCheck = Tkinter.Checkbutton(root,fg=fgColor, text = "Chords", font=("Arial", 10), variable = self.hasChords, onvalue = 1, offvalue = 0)
        self.arpeggioCheck = Tkinter.Checkbutton(root,fg=fgColor, text = "Arpeggio", font=("Arial", 10), variable = self.hasArpeggio, onvalue = 1, offvalue = 0)
        self.bassCheck = Tkinter.Checkbutton(root,fg=fgColor, text = "Bass", font=("Arial", 10), variable = self.hasBass, onvalue = 1, offvalue = 0)
        self.voice1Check = Tkinter.Checkbutton(root,fg=fgColor, text = "Melody", font=("Arial", 10), variable = self.hasVoice1, onvalue = 1, offvalue = 0)
        self.voice5Check = Tkinter.Checkbutton(root,fg=fgColor, text = "Guitar 5", font=("Arial", 10), variable = self.hasVoice5, onvalue = 1, offvalue = 0)
        self.voice4Check = Tkinter.Checkbutton(root,fg=fgColor, text = "Guitar 4", font=("Arial", 10), variable = self.hasVoice4, onvalue = 1, offvalue = 0)
        self.voice3Check = Tkinter.Checkbutton(root,fg=fgColor, text = "Guitar 3", font=("Arial", 10), variable = self.hasVoice3, onvalue = 1, offvalue = 0)
        self.voice2Check = Tkinter.Checkbutton(root,fg=fgColor, text = "Guitar 2", font=("Arial", 10), variable = self.hasVoice2, onvalue = 1, offvalue = 0)
        self.chordsCheck.grid(row=11, column=2, sticky="w")
        self.bassCheck.grid(row=12, column=2, sticky="w")
        self.arpeggioCheck.grid(row=13, column=2, sticky="w")
        self.voice1Check.grid(row=14, column=2, sticky="w")
        self.voice5Check.grid(row=15, column=2, sticky="w")
        self.voice4Check.grid(row=16, column=2, sticky="w")
        self.voice3Check.grid(row=17, column=2, sticky="w")
        self.voice2Check.grid(row=18, column=2, sticky="w")
        #Initialisation
        #self.voice1Check.select()
        self.voice5Check.select()
        self.voice4Check.select()
        #self.bassCheck.select()
        self.arpeggioCheck.select()

        presenceText = Tkinter.Label(root, text="\nVoices presence:  ", font=("Arial", 10), fg=fgColor)
        presenceText.grid(row=14, column=3, sticky="w")
        self.voice5scale = Tkinter.Scale(root, fg=fgColor,bg=bgColor, from_=0, to=100, orient=Tkinter.HORIZONTAL, length=200)
        self.voice4scale = Tkinter.Scale(root, fg=fgColor,bg=bgColor, from_=0, to=100, orient=Tkinter.HORIZONTAL, length=200)
        self.voice3scale = Tkinter.Scale(root, fg=fgColor,bg=bgColor, from_=0, to=100, orient=Tkinter.HORIZONTAL, length=200)
        self.voice2scale = Tkinter.Scale(root, fg=fgColor,bg=bgColor, from_=0, to=100, orient=Tkinter.HORIZONTAL, length=200)
        self.voice5scale.grid(row=15, column=3)
        self.voice4scale.grid(row=16, column=3)
        self.voice3scale.grid(row=17, column=3)
        self.voice2scale.grid(row=18, column=3)
        self.voice5scale.set(30)
        self.voice4scale.set(50)
        self.voice3scale.set(0)
        self.voice2scale.set(0)

        #Play
        self.playButton=Tkinter.Button(root,text="  Play!  ", font=("Arial", 16), command=self.onPlayClick, bg=bgColor, fg=fgColor)
        self.playButton.grid(row=20, column=3)

        #Random
        randomButton=Tkinter.Button(root,text=" Randomize! ", font=("Arial", 12), command=self.onRandomClick, bg=bgColor, fg=fgColor)
        randomButton.grid(row=20, column=2)

        #Change Chords
        changeChordsButton=Tkinter.Button(root,text=" Change Chords ", font=("Arial", 10), command=self.onChangeChordsClick, bg=bgColor, fg=fgColor)		
        changeBassButton=Tkinter.Button(root,text=" Change Pattern ", font=("Arial", 10), command=self.onChangeArpeggioClick, bg=bgColor, fg=fgColor)
        changeArpeggioButton=Tkinter.Button(root,text=" Change Pattern ", font=("Arial", 10), command=self.onChangeBassClick, bg=bgColor, fg=fgColor)
        changeChordsButton.grid(row=11,column=3, sticky= "w")
        changeArpeggioButton.grid(row=12,column=3, sticky= "w")
        changeBassButton.grid(row=13,column=3, sticky= "w")
			
			
        #Advanced parameters
        advancedButton=Tkinter.Button(root,text=" Advanced Options ", font=("Arial", 10), command=self.onAdvancedClick, bg=bgColor, fg=fgColor)
        advancedButton.grid(row=1,column=3, sticky= "e")
		
        #Advanced patterns
        self.advancedPattern=Tkinter.Button(root,text=" Custom Patterns ", font=("Arial", 10), command=self.onAdvancedPatternClick, bg=bgColor, fg=fgColor)
        self.spaceAdvanced = Tkinter.Label(root, text="    ", font=("Arial",14))
        self.spaceAdvanced2 = Tkinter.Label(root, text="                         ", font=("Arial",14))
		
		#Poetry
        self.writePoetry=Tkinter.IntVar()
        self.poetryCheck = Tkinter.Checkbutton(root,fg=fgColor, text = "Poetry", font=("Arial", 10), variable = self.writePoetry, onvalue = 1, offvalue = 0)
        self.poetryCheck.select()
		
        #Melody Options
        self.melodicDisonanceModeButton=Tkinter.Button(root,text="  Melody Options  ", font=("Arial", 10), command=self.onMelodyOptionsClick, bg=bgColor, fg=fgColor)
 
        self.melodicDisonanceMode=Tkinter.IntVar()
        self.melodicDisonanceModeCheck = Tkinter.Checkbutton(root,fg=fgColor, text = "Force dissonance limits", font=("Arial", 10), variable = self.melodicDisonanceMode, onvalue = 1, offvalue = 0)
        self.dissonanceInfLimitText = Tkinter.Label(root, text="Min:", font=("Arial", 10), fg=fgColor)
        self.dissonanceSupLimitText = Tkinter.Label(root, text="Max:", font=("Arial", 10), fg=fgColor)
        self.dissonanceInfLimitScale = Tkinter.Scale(root, fg=fgColor,bg=bgColor, from_=0.0, to=8.0, resolution=0.01, orient=Tkinter.HORIZONTAL, length=118)
        self.dissonanceSupLimitScale = Tkinter.Scale(root, fg=fgColor,bg=bgColor, from_=0.0, to=8.0, resolution=0.01, orient=Tkinter.HORIZONTAL, length=118)
        self.dissonanceInfLimitScale.set(2.0)
        self.dissonanceSupLimitScale.set(4.0)
		
        self.outOfChordScaleText = Tkinter.Label(root, text="    % Out of\n        Chord:", font=("Arial", 10), fg=fgColor)
        self.outOfChordScale = Tkinter.Scale(root, fg=fgColor,bg=bgColor, from_=0, to=100, resolution=1, orient=Tkinter.HORIZONTAL, length=118)
        self.outOfChordScale.set(33)
		
        self.periodicChangeMode=Tkinter.IntVar()
        self.periodicChangeCheck = Tkinter.Checkbutton(root,fg=fgColor, text = "Periodic Changes", font=("Arial", 10), variable = self.periodicChangeMode, onvalue = 1, offvalue = 0)
        self.periodicChangeCheck.select()
		
        self.waitForChanges=Tkinter.IntVar()
        self.waitForChangesCheck = Tkinter.Checkbutton(root,fg=fgColor, text = "Hold Changes", font=("Arial", 10), variable = self.waitForChanges, onvalue = 1, offvalue = 0)
        self.waitForChangesCheck.deselect()		

        #Keyboard
        self.testKeyboardButton=Tkinter.Button(root,text="   Test Keyboard  ", font=("Arial", 10), command=self.onTestKeyboardClick, bg=bgColor, fg=fgColor)
        #self.testKeyboardButton.grid(row=2,column=3, sticky= "e")
		
		
        #self.changeKeyButton=Tkinter.Button(root,text=" Set new Key and scales ", font=("Arial", 10), command=self.onChangeKeyClick, bg=bgColor, fg=fgColor)
        #Keyboard
        self.spaceTestKeyboard = Tkinter.Label(root, text="    ", font=("Arial",14))
        self.C5 = Tkinter.Button(root,text=" C5 ", font=("Arial", 10), command=lambda: self.playNote("C5"), bg=bgColor, fg=fgColor)
        self.Db5 = Tkinter.Button(root,text=" C#5 ", font=("Arial", 10), command=lambda: self.playNote("C#5"), bg=bgColor, fg=fgColor)
        self.D5 = Tkinter.Button(root,text=" D5 ", font=("Arial", 10), command=lambda: self.playNote("D5"), bg=bgColor, fg=fgColor)
        self.Eb5 = Tkinter.Button(root,text=" D#5 ", font=("Arial", 10), command=lambda: self.playNote("D#5"), bg=bgColor, fg=fgColor)
        self.E5 = Tkinter.Button(root,text=" E5 ", font=("Arial", 10), command=lambda: self.playNote("E5"), bg=bgColor, fg=fgColor)
        self.F5 = Tkinter.Button(root,text=" F5 ", font=("Arial", 10), command=lambda: self.playNote("F5"), bg=bgColor, fg=fgColor)
        self.Gb5 = Tkinter.Button(root,text=" F#5 ", font=("Arial", 10), command=lambda: self.playNote("F#5"), bg=bgColor, fg=fgColor)
        self.G5 = Tkinter.Button(root,text=" G5 ", font=("Arial", 10), command=lambda: self.playNote("G5"), bg=bgColor, fg=fgColor)
        self.Ab5 = Tkinter.Button(root,text=" G#5 ", font=("Arial", 10), command=lambda: self.playNote("G#5"), bg=bgColor, fg=fgColor)
        self.A5 = Tkinter.Button(root,text=" A5 ", font=("Arial", 10), command=lambda: self.playNote("A5"), bg=bgColor, fg=fgColor)
        self.Bb5 = Tkinter.Button(root,text=" A#5 ", font=("Arial", 10), command=lambda: self.playNote("A#5"), bg=bgColor, fg=fgColor)
        self.B5 = Tkinter.Button(root,text=" B5 ", font=("Arial", 10), command=lambda: self.playNote("B5"), bg=bgColor, fg=fgColor)

        self.C4 = Tkinter.Button(root,text=" C4 ", font=("Arial", 10), command=lambda: self.playNote("C4"), bg=bgColor, fg=fgColor)
        self.Db4 = Tkinter.Button(root,text=" C#4 ", font=("Arial", 10), command=lambda: self.playNote("C#4"), bg=bgColor, fg=fgColor)
        self.D4 = Tkinter.Button(root,text=" D4 ", font=("Arial", 10), command=lambda: self.playNote("D4"), bg=bgColor, fg=fgColor)
        self.Eb4 = Tkinter.Button(root,text=" D#4 ", font=("Arial", 10), command=lambda: self.playNote("D#4"), bg=bgColor, fg=fgColor)
        self.E4 = Tkinter.Button(root,text=" E4 ", font=("Arial", 10), command=lambda: self.playNote("E4"), bg=bgColor, fg=fgColor)
        self.F4 = Tkinter.Button(root,text=" F4 ", font=("Arial", 10), command=lambda: self.playNote("F4"), bg=bgColor, fg=fgColor)
        self.Gb4 = Tkinter.Button(root,text=" F#4 ", font=("Arial", 10), command=lambda: self.playNote("F#4"), bg=bgColor, fg=fgColor)
        self.G4 = Tkinter.Button(root,text=" G4 ", font=("Arial", 10), command=lambda: self.playNote("G4"), bg=bgColor, fg=fgColor)
        self.Ab4 = Tkinter.Button(root,text=" G#4 ", font=("Arial", 10), command=lambda: self.playNote("G#4"), bg=bgColor, fg=fgColor)
        self.A4 = Tkinter.Button(root,text=" A4 ", font=("Arial", 10), command=lambda: self.playNote("A4"), bg=bgColor, fg=fgColor)
        self.Bb4 = Tkinter.Button(root,text=" A#4 ", font=("Arial", 10), command=lambda: self.playNote("A#4"), bg=bgColor, fg=fgColor)
        self.B4 = Tkinter.Button(root,text=" B4 ", font=("Arial", 10), command=lambda: self.playNote("B4"), bg=bgColor, fg=fgColor)

        self.C3 = Tkinter.Button(root,text=" C3 ", font=("Arial", 10), command=lambda: self.playNote("C3"), bg=bgColor, fg=fgColor)
        self.Db3 = Tkinter.Button(root,text=" C#3 ", font=("Arial", 10), command=lambda: self.playNote("C#3"), bg=bgColor, fg=fgColor)
        self.D3 = Tkinter.Button(root,text=" D3 ", font=("Arial", 10), command=lambda: self.playNote("D3"), bg=bgColor, fg=fgColor)
        self.Eb3 = Tkinter.Button(root,text=" D#3 ", font=("Arial", 10), command=lambda: self.playNote("D#3"), bg=bgColor, fg=fgColor)
        self.E3 = Tkinter.Button(root,text=" E3 ", font=("Arial", 10), command=lambda: self.playNote("E3"), bg=bgColor, fg=fgColor)
        self.F3 = Tkinter.Button(root,text=" F3 ", font=("Arial", 10), command=lambda: self.playNote("F3"), bg=bgColor, fg=fgColor)
        self.Gb3 = Tkinter.Button(root,text=" F#3 ", font=("Arial", 10), command=lambda: self.playNote("F#3"), bg=bgColor, fg=fgColor)
        self.G3 = Tkinter.Button(root,text=" G3 ", font=("Arial", 10), command=lambda: self.playNote("G3"), bg=bgColor, fg=fgColor)
        self.Ab3 = Tkinter.Button(root,text=" G#3 ", font=("Arial", 10), command=lambda: self.playNote("G#3"), bg=bgColor, fg=fgColor)
        self.A3 = Tkinter.Button(root,text=" A3 ", font=("Arial", 10), command=lambda: self.playNote("A3"), bg=bgColor, fg=fgColor)
        self.Bb3 = Tkinter.Button(root,text=" A#3 ", font=("Arial", 10), command=lambda: self.playNote("A#3"), bg=bgColor, fg=fgColor)
        self.B3 = Tkinter.Button(root,text=" B3 ", font=("Arial", 10), command=lambda: self.playNote("B3"), bg=bgColor, fg=fgColor)

        self.C2 = Tkinter.Button(root,text=" C2 ", font=("Arial", 10), command=lambda: self.playNote("C2"), bg=bgColor, fg=fgColor)
        self.Db2 = Tkinter.Button(root,text=" C#2 ", font=("Arial", 10), command=lambda: self.playNote("C#2"), bg=bgColor, fg=fgColor)
        self.D2 = Tkinter.Button(root,text=" D2 ", font=("Arial", 10), command=lambda: self.playNote("D2"), bg=bgColor, fg=fgColor)
        self.Eb2 = Tkinter.Button(root,text=" D#2 ", font=("Arial", 10), command=lambda: self.playNote("D#2"), bg=bgColor, fg=fgColor)
        self.E2 = Tkinter.Button(root,text=" E2 ", font=("Arial", 10), command=lambda: self.playNote("E2"), bg=bgColor, fg=fgColor)
        self.F2 = Tkinter.Button(root,text=" F2 ", font=("Arial", 10), command=lambda: self.playNote("F2"), bg=bgColor, fg=fgColor)
        self.Gb2 = Tkinter.Button(root,text=" F#2 ", font=("Arial", 10), command=lambda: self.playNote("F#2"), bg=bgColor, fg=fgColor)
        self.G2 = Tkinter.Button(root,text=" G2 ", font=("Arial", 10), command=lambda: self.playNote("G2"), bg=bgColor, fg=fgColor)
        self.Ab2 = Tkinter.Button(root,text=" G#2 ", font=("Arial", 10), command=lambda: self.playNote("G#2"), bg=bgColor, fg=fgColor)
        self.A2 = Tkinter.Button(root,text=" A2 ", font=("Arial", 10), command=lambda: self.playNote("A2"), bg=bgColor, fg=fgColor)
        self.Bb2 = Tkinter.Button(root,text=" A#2 ", font=("Arial", 10), command=lambda: self.playNote("A#2"), bg=bgColor, fg=fgColor)
        self.B2 = Tkinter.Button(root,text=" B2 ", font=("Arial", 10), command=lambda: self.playNote("B2"), bg=bgColor, fg=fgColor)

        self.CM = Tkinter.Button(root,text=" CM ", font=("Arial", 10), command=lambda: self.playChord("CM"), bg=bgColor, fg=fgColor)
        self.DbM = Tkinter.Button(root,text=" C#M ", font=("Arial", 10), command=lambda: self.playChord("C#M"), bg=bgColor, fg=fgColor)
        self.DM = Tkinter.Button(root,text=" DM ", font=("Arial", 10), command=lambda: self.playChord("DM"), bg=bgColor, fg=fgColor)
        self.EbM = Tkinter.Button(root,text=" D#M ", font=("Arial", 10), command=lambda: self.playChord("D#M"), bg=bgColor, fg=fgColor)
        self.EM = Tkinter.Button(root,text=" EM ", font=("Arial", 10), command=lambda: self.playChord("EM"), bg=bgColor, fg=fgColor)
        self.FM = Tkinter.Button(root,text=" FM ", font=("Arial", 10), command=lambda: self.playChord("FM"), bg=bgColor, fg=fgColor)
        self.GbM = Tkinter.Button(root,text=" F#M ", font=("Arial", 10), command=lambda: self.playChord("F#M"), bg=bgColor, fg=fgColor)
        self.GM = Tkinter.Button(root,text=" GM ", font=("Arial", 10), command=lambda: self.playChord("GM"), bg=bgColor, fg=fgColor)
        self.AbM = Tkinter.Button(root,text=" G#M ", font=("Arial", 10), command=lambda: self.playChord("G#M"), bg=bgColor, fg=fgColor)
        self.AM = Tkinter.Button(root,text=" AM ", font=("Arial", 10), command=lambda: self.playChord("AM"), bg=bgColor, fg=fgColor)
        self.BbM = Tkinter.Button(root,text=" A#M ", font=("Arial", 10), command=lambda: self.playChord("A#M"), bg=bgColor, fg=fgColor)
        self.BM = Tkinter.Button(root,text=" BM ", font=("Arial", 10), command=lambda: self.playChord("BM"), bg=bgColor, fg=fgColor)

        self.Cm = Tkinter.Button(root,text=" Cm ", font=("Arial", 10), command=lambda: self.playChord("Cm"), bg=bgColor, fg=fgColor)
        self.Dbm = Tkinter.Button(root,text=" C#m ", font=("Arial", 10), command=lambda: self.playChord("C#m"), bg=bgColor, fg=fgColor)
        self.Dm = Tkinter.Button(root,text=" Dm ", font=("Arial", 10), command=lambda: self.playChord("Dm"), bg=bgColor, fg=fgColor)
        self.Ebm = Tkinter.Button(root,text=" D#m ", font=("Arial", 10), command=lambda: self.playChord("D#m"), bg=bgColor, fg=fgColor)
        self.Em = Tkinter.Button(root,text=" Em ", font=("Arial", 10), command=lambda: self.playChord("Em"), bg=bgColor, fg=fgColor)
        self.Fm = Tkinter.Button(root,text=" Fm ", font=("Arial", 10), command=lambda: self.playChord("Fm"), bg=bgColor, fg=fgColor)
        self.Gbm = Tkinter.Button(root,text=" F#m ", font=("Arial", 10), command=lambda: self.playChord("F#m"), bg=bgColor, fg=fgColor)
        self.Gm = Tkinter.Button(root,text=" Gm ", font=("Arial", 10), command=lambda: self.playChord("Gm"), bg=bgColor, fg=fgColor)
        self.Abm = Tkinter.Button(root,text=" G#m ", font=("Arial", 10), command=lambda: self.playChord("G#m"), bg=bgColor, fg=fgColor)
        self.Am = Tkinter.Button(root,text=" Am ", font=("Arial", 10), command=lambda: self.playChord("Am"), bg=bgColor, fg=fgColor)
        self.Bbm = Tkinter.Button(root,text=" A#m ", font=("Arial", 10), command=lambda: self.playChord("A#m"), bg=bgColor, fg=fgColor)
        self.Bm = Tkinter.Button(root,text=" Bm ", font=("Arial", 10), command=lambda: self.playChord("Bm"), bg=bgColor, fg=fgColor)
		
        self.Cdim = Tkinter.Button(root,text="Cdim", font=("Arial", 10), command=lambda: self.playChord("Cdim"), bg=bgColor, fg=fgColor)
        self.Dbdim = Tkinter.Button(root,text="C#dim", font=("Arial", 10), command=lambda: self.playChord("C#dim"), bg=bgColor, fg=fgColor)
        self.Ddim = Tkinter.Button(root,text="Ddim", font=("Arial", 10), command=lambda: self.playChord("Ddim"), bg=bgColor, fg=fgColor)
        self.Ebdim = Tkinter.Button(root,text="D#dim", font=("Arial", 10), command=lambda: self.playChord("D#dim"), bg=bgColor, fg=fgColor)
        self.Edim = Tkinter.Button(root,text="Edim", font=("Arial", 10), command=lambda: self.playChord("Edim"), bg=bgColor, fg=fgColor)
        self.Fdim = Tkinter.Button(root,text="Fdim", font=("Arial", 10), command=lambda: self.playChord("Fdim"), bg=bgColor, fg=fgColor)
        self.Gbdim = Tkinter.Button(root,text="F#dim", font=("Arial", 10), command=lambda: self.playChord("F#dim"), bg=bgColor, fg=fgColor)
        self.Gdim = Tkinter.Button(root,text="Gdim", font=("Arial", 10), command=lambda: self.playChord("Gdim"), bg=bgColor, fg=fgColor)
        self.Abdim = Tkinter.Button(root,text="G#dim", font=("Arial", 10), command=lambda: self.playChord("G#dim"), bg=bgColor, fg=fgColor)
        self.Adim = Tkinter.Button(root,text="Adim", font=("Arial", 10), command=lambda: self.playChord("Adim"), bg=bgColor, fg=fgColor)
        self.Bbdim = Tkinter.Button(root,text="A#dim", font=("Arial", 10), command=lambda: self.playChord("A#dim"), bg=bgColor, fg=fgColor)
        self.Bdim = Tkinter.Button(root,text="Bdim", font=("Arial", 10), command=lambda: self.playChord("Bdim"), bg=bgColor, fg=fgColor)
		
		
		
		
		#Advanced options
        self.spacePattern = Tkinter.Label(root, text="    ", font=("Arial",14))
        self.setProgressionText = Tkinter.Label(root, text="Custom Chords:", font=("Arial",10), fg=fgColor)
        self.setArpeggioText = Tkinter.Label(root, text="Custom Arpeggio:", font=("Arial",10), fg=fgColor)
        self.setBassText = Tkinter.Label(root, text="Custom Bass:", font=("Arial",10), fg=fgColor)
		
        self.setArpeggio = Tkinter.Button(root,text=" Set ", font=("Arial", 10), command=lambda: self.onSetArpeggioApplyClick(self.compassBeats,self.userArpeggio), bg=bgColor, fg=fgColor)
        self.setArpeggio0 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(0), bg=bgColor, fg=fgColor)
        self.setArpeggio1 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(1), bg=bgColor, fg=fgColor)
        self.setArpeggio2 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(2), bg=bgColor, fg=fgColor)
        self.setArpeggio3 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(3), bg=bgColor, fg=fgColor)
        self.setArpeggio4 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(4), bg=bgColor, fg=fgColor)
        self.setArpeggio5 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(5), bg=bgColor, fg=fgColor)
        self.setArpeggio6 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(6), bg=bgColor, fg=fgColor)
        self.setArpeggio7 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(7), bg=bgColor, fg=fgColor)
        self.setArpeggio8 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(8), bg=bgColor, fg=fgColor)
        self.setArpeggio9 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(9), bg=bgColor, fg=fgColor)
        self.setArpeggio10 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(10), bg=bgColor, fg=fgColor)
        self.setArpeggio11 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(11), bg=bgColor, fg=fgColor)
        self.setArpeggio12 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(12), bg=bgColor, fg=fgColor)
        self.setArpeggio13 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(13), bg=bgColor, fg=fgColor)
        self.setArpeggio14 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(14), bg=bgColor, fg=fgColor)
        self.setArpeggio15 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetArpeggioClick(15), bg=bgColor, fg=fgColor)
		
        self.setBass = Tkinter.Button(root,text=" Set ", font=("Arial", 10), command=lambda: self.onSetBassApplyClick(self.compassBeats,self.userBass), bg=bgColor, fg=fgColor)
        self.setBass0 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(0), bg=bgColor, fg=fgColor)
        self.setBass1 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(1), bg=bgColor, fg=fgColor)
        self.setBass2 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(2), bg=bgColor, fg=fgColor)
        self.setBass3 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(3), bg=bgColor, fg=fgColor)
        self.setBass4 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(4), bg=bgColor, fg=fgColor)
        self.setBass5 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(5), bg=bgColor, fg=fgColor)
        self.setBass6 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(6), bg=bgColor, fg=fgColor)
        self.setBass7 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(7), bg=bgColor, fg=fgColor)
        self.setBass8 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(8), bg=bgColor, fg=fgColor)
        self.setBass9 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(9), bg=bgColor, fg=fgColor)
        self.setBass10 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(10), bg=bgColor, fg=fgColor)
        self.setBass11 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(11), bg=bgColor, fg=fgColor)
        self.setBass12 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(12), bg=bgColor, fg=fgColor)
        self.setBass13 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(13), bg=bgColor, fg=fgColor)
        self.setBass14 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(14), bg=bgColor, fg=fgColor)
        self.setBass15 = Tkinter.Button(root,text="    ", font=("Arial", 10), command=lambda: self.onSetBassClick(15), bg=bgColor, fg=fgColor)
		
        self.setChords = Tkinter.Button(root,text="Set", font=("Arial", 10), command= self.onSetChordsApplyClick, bg=bgColor, fg=fgColor)
        self.setChord0= Tkinter.Button(root,text="I", font=("Arial", 10), command=lambda: self.onSetChordClick(0,self.mode), bg=bgColor, fg=fgColor)
        self.setChord1= Tkinter.Button(root,text="I", font=("Arial", 10), command=lambda: self.onSetChordClick(1,self.mode), bg=bgColor, fg=fgColor)
        self.setChord2= Tkinter.Button(root,text="I", font=("Arial", 10), command=lambda: self.onSetChordClick(2,self.mode), bg=bgColor, fg=fgColor)
        self.setChord3= Tkinter.Button(root,text="I", font=("Arial", 10), command=lambda: self.onSetChordClick(3,self.mode), bg=bgColor, fg=fgColor)
        self.setChord4= Tkinter.Button(root,text="I", font=("Arial", 10), command=lambda: self.onSetChordClick(4,self.mode), bg=bgColor, fg=fgColor)
        self.setChord5= Tkinter.Button(root,text="I", font=("Arial", 10), command=lambda: self.onSetChordClick(5,self.mode), bg=bgColor, fg=fgColor)
        self.setChord6= Tkinter.Button(root,text="I", font=("Arial", 10), command=lambda: self.onSetChordClick(6,self.mode), bg=bgColor, fg=fgColor)
        self.setChord7= Tkinter.Button(root,text="I", font=("Arial", 10), command=lambda: self.onSetChordClick(7,self.mode), bg=bgColor, fg=fgColor)
        self.setChord0.config(width=2)
        self.setChord1.config(width=2)
        self.setChord2.config(width=2)
        self.setChord3.config(width=2)
        self.setChord4.config(width=2)
        self.setChord5.config(width=2)
        self.setChord6.config(width=2)
        self.setChord7.config(width=2)
		

		
        root.mainloop()
    
    def onPlayClick(self):
        self.initPlay()

    def onStopClick(self):
        self.lyricsCount=0
        self.playing=False
        self.playButton.config(text="Play!", command=self.onPlayClick)

    def onRandomClick(self):
        #TODO: Select from pre-defined subsets
        self.guiKey.set(random.choice(["A","A#","B","C","C#","D","D#","E","F","F#","G","G#"]))
        self.guiChords.set(random.choice([ "Major", "Natural Minor", "Melodic Minor","Harmonic Minor"]))
        rand=random.choice([0,1,2])
        if self.guiChords.get()== "Major" and (not rand):
            if rand==1:
                self.guiScale.set("Pentatonic Major")
            else:
                self.guiScale.set("Blues Major")
        elif (not rand):
            if rand==1:
                self.guiScale.set("Pentatonic Minor")
            else:
                self.guiScale.set("Blues Minor")
        else:
            self.guiScale.set(self.guiChords.get())
        
        if random.choice([1,1,1]):#Chords, never
            self.chordsCheck.deselect()
        else:
            self.chordsCheck.select()

        if random.choice([0,0,0,1]):#Arpeggio
            self.arpeggioCheck.deselect()
        else:
            self.arpeggioCheck.select()
        if random.choice([0,1]):#Bass
            self.bassCheck.deselect()
        else:
            self.bassCheck.select()

        if random.choice([0,0,1]):#Melody
            self.voice1Check.deselect()
            if random.choice([0,0,1]):#Bass
                self.bassCheck.deselect()
            else:
                self.bassCheck.select()	
            if random.choice([0,1]):#Voice5
                self.voice5Check.deselect()
            else:
                self.voice5Check.select()
            if random.choice([0,0,1]):#Voice4
                self.voice4Check.deselect()
            else:
                self.voice4Check.select()
            if random.choice([0,1]):#Voice3
                self.voice3Check.deselect()
            else:
                self.voice3Check.select()
            if random.choice([0,1,1,1]):#Voice2
                self.voice2Check.deselect()
            else:
                self.voice2Check.select()
        else:
            self.voice1Check.select()

            if random.choice([0,1,1]):#Voice5
                self.voice5Check.deselect()
            else:
                self.voice5Check.select()
            if random.choice([0,1,1,1]):#Voice4
                self.voice4Check.deselect()
            else:
                self.voice4Check.select()
            if random.choice([0,1,1,1,1]):#Voice3
                self.voice3Check.deselect()
            else:
                self.voice3Check.select()
            if random.choice([1,1,1]):#Voice2, never with melody
                self.voice2Check.deselect()
            else:
                self.voice2Check.select()


        self.voice5scale.set(random.randint(20,60))
        self.voice4scale.set(random.randint(20,60))
        self.voice3scale.set(random.randint(10,50))
        self.voice2scale.set(random.randint(10,50))
        self.tempoScale.set(random.uniform(0.2,0.35))
        self.beatsScale.set(random.choice([4,6,8,8,8,10,12,12,12,16]))

    def onAdvancedClick(self):
        if self.advancedFlag:
            self.advancedFlag=False
            self.spaceAdvanced.grid_remove()
            self.spaceAdvanced2.grid_remove()
            self.advancedPattern.grid_remove()
            self.melodicDisonanceModeButton.grid_remove()
            self.testKeyboardButton.grid_remove()
            self.poetryCheck.grid_remove()
            self.removePatternOptions()
            if self.advancedPatternFlag:
                self.advancedPatternFlag=not self.advancedPatternFlag
            self.removeMelodyOptions()
            if self.melodyButtonFlag:
                self.melodyButtonFlag=not self.melodyButtonFlag
            self.removeKeyboard()
        else:
            self.advancedFlag=True
            self.advancedPattern.grid(row=2,column=4, sticky= "e")
            self.melodicDisonanceModeButton.grid(row=1,column=4, sticky= "e")
            self.testKeyboardButton.grid(row=3,column=4, sticky= "e")
            self.poetryCheck.grid(row=4,column=4, sticky= "n")
            self.spaceAdvanced.grid(row=1,column=50, sticky= "e")
            self.spaceAdvanced2.grid(row=50,column=4, sticky= "e")
            self.removeKeyboard()
            if self.testKeyboardFlag:
                self.testKeyboardFlag=not self.testKeyboardFlag

    def onMelodyOptionsClick(self):
        if self.melodyButtonFlag:
            self.melodyButtonFlag=False
            self.removeMelodyOptions()
        else:
            self.melodyButtonFlag=True
            self.outOfChordScaleText.grid(row=1, column=5, sticky="nw")
            self.outOfChordScale.grid(row=1, column=6, sticky="nw")
            self.periodicChangeCheck.grid(row=1,column=7, sticky="nw")
            self.periodicChangeCheck.select()
            self.waitForChangesCheck.grid(row=2,column=7, sticky="nw")
            self.melodicDisonanceModeCheck.grid(row=3, column=6, sticky="nw")
            self.dissonanceInfLimitText.grid(row=4, column=5, sticky="ne")
            self.dissonanceSupLimitText.grid(row=5, column=5, sticky="ne")
            self.dissonanceInfLimitScale.grid(row=4, column=6, sticky="nw")
            self.dissonanceSupLimitScale.grid(row=5, column=6, sticky="nw")

            self.removeKeyboard()
            if self.testKeyboardFlag:
                self.testKeyboardFlag=not self.testKeyboardFlag
            self.removePatternOptions()
            if self.advancedPatternFlag:
                self.advancedPatternFlag=not self.advancedPatternFlag
			
    def onTestKeyboardClick(self):
        if self.testKeyboardFlag:
            self.testKeyboardFlag=False
            self.removeKeyboard()
        else:
            self.testKeyboardFlag=True
			
			#Remove advanced options GUI
            #self.spaceAdvanced.grid_remove()
            #self.spaceAdvanced2.grid_remove()
            #self.advancedPattern.grid_remove()
            self.removePatternOptions()
            if self.advancedPatternFlag:
                self.advancedPatternFlag=not self.advancedPatternFlag
            self.removeMelodyOptions()
            if self.melodyButtonFlag:
                self.melodyButtonFlag=not self.melodyButtonFlag
				
            self.C5.grid(row=1,column=23, sticky= "sw")
            self.Db5.grid(row=1,column=24, sticky= "sw")
            self.D5.grid(row=1,column=25, sticky= "sw")
            self.Eb5.grid(row=1,column=26, sticky= "sw")
            self.E5.grid(row=1,column=27, sticky= "sw")
            self.F5.grid(row=1,column=28, sticky= "sw")
            self.Gb5.grid(row=1,column=29, sticky= "sw")
            self.G5.grid(row=1,column=30, sticky= "sw")
            self.Ab5.grid(row=1,column=31, sticky= "sw")
            self.A5.grid(row=1,column=32, sticky= "sw")
            self.Bb5.grid(row=1,column=33, sticky= "sw")
            self.B5.grid(row=1,column=34, sticky= "sw")
			
            self.C4.grid(row=2,column=23, sticky= "nw")
            self.Db4.grid(row=2,column=24, sticky= "nw")
            self.D4.grid(row=2,column=25, sticky= "nw")
            self.Eb4.grid(row=2,column=26, sticky= "nw")
            self.E4.grid(row=2,column=27, sticky= "nw")
            self.F4.grid(row=2,column=28, sticky= "nw")
            self.Gb4.grid(row=2,column=29, sticky= "nw")
            self.G4.grid(row=2,column=30, sticky= "nw")
            self.Ab4.grid(row=2,column=31, sticky= "nw")
            self.A4.grid(row=2,column=32, sticky= "nw")
            self.Bb4.grid(row=2,column=33, sticky= "nw")
            self.B4.grid(row=2,column=34, sticky= "nw")
			
            self.C3.grid(row=3,column=23, sticky= "nw")
            self.Db3.grid(row=3,column=24, sticky= "nw")
            self.D3.grid(row=3,column=25, sticky= "nw")
            self.Eb3.grid(row=3,column=26, sticky= "nw")
            self.E3.grid(row=3,column=27, sticky= "nw")
            self.F3.grid(row=3,column=28, sticky= "nw")
            self.Gb3.grid(row=3,column=29, sticky= "nw")
            self.G3.grid(row=3,column=30, sticky= "nw")
            self.Ab3.grid(row=3,column=31, sticky= "nw")
            self.A3.grid(row=3,column=32, sticky= "nw")
            self.Bb3.grid(row=3,column=33, sticky= "nw")
            self.B3.grid(row=3,column=34, sticky= "nw")
			
            self.C2.grid(row=4,column=23, sticky= "nw")
            self.Db2.grid(row=4,column=24, sticky= "nw")
            self.D2.grid(row=4,column=25, sticky= "nw")
            self.Eb2.grid(row=4,column=26, sticky= "nw")
            self.E2.grid(row=4,column=27, sticky= "nw")
            self.F2.grid(row=4,column=28, sticky= "nw")
            self.Gb2.grid(row=4,column=29, sticky= "nw")
            self.G2.grid(row=4,column=30, sticky= "nw")
            self.Ab2.grid(row=4,column=31, sticky= "nw")
            self.A2.grid(row=4,column=32, sticky= "nw")
            self.Bb2.grid(row=4,column=33, sticky= "nw")
            self.B2.grid(row=4,column=34, sticky= "nw")
			
            self.CM.grid(row=5,column=23, sticky= "sw")
            self.DbM.grid(row=5,column=24, sticky= "sw")
            self.DM.grid(row=5,column=25, sticky= "sw")
            self.EbM.grid(row=5,column=26, sticky= "sw")
            self.EM.grid(row=5,column=27, sticky= "sw")
            self.FM.grid(row=5,column=28, sticky= "sw")
            self.GbM.grid(row=5,column=29, sticky= "sw")
            self.GM.grid(row=5,column=30, sticky= "sw")
            self.AbM.grid(row=5,column=31, sticky= "sw")
            self.AM.grid(row=5,column=32, sticky= "sw")
            self.BbM.grid(row=5,column=33, sticky= "sw")
            self.BM.grid(row=5,column=34, sticky= "sw")
			
            self.Cm.grid(row=6,column=23, sticky= "nw")
            self.Dbm.grid(row=6,column=24, sticky= "nw")
            self.Dm.grid(row=6,column=25, sticky= "nw")
            self.Ebm.grid(row=6,column=26, sticky= "nw")
            self.Em.grid(row=6,column=27, sticky= "nw")
            self.Fm.grid(row=6,column=28, sticky= "nw")
            self.Gbm.grid(row=6,column=29, sticky= "nw")
            self.Gm.grid(row=6,column=30, sticky= "nw")
            self.Abm.grid(row=6,column=31, sticky= "nw")
            self.Am.grid(row=6,column=32, sticky= "nw")
            self.Bbm.grid(row=6,column=33, sticky= "nw")
            self.Bm.grid(row=6,column=34, sticky= "nw")
			
            self.Cdim.grid(row=7,column=23, sticky= "nw")
            self.Dbdim.grid(row=7,column=24, sticky= "nw")
            self.Ddim.grid(row=7,column=25, sticky= "nw")
            self.Ebdim.grid(row=7,column=26, sticky= "nw")
            self.Edim.grid(row=7,column=27, sticky= "nw")
            self.Fdim.grid(row=7,column=28, sticky= "nw")
            self.Gbdim.grid(row=7,column=29, sticky= "nw")
            self.Gdim.grid(row=7,column=30, sticky= "nw")
            self.Abdim.grid(row=7,column=31, sticky= "nw")
            self.Adim.grid(row=7,column=32, sticky= "nw")
            self.Bbdim.grid(row=7,column=33, sticky= "nw")
            self.Bdim.grid(row=7,column=34, sticky= "nw")
			
            self.spaceTestKeyboard.grid(row=1, column=50)#TODO: Change col

    def onAdvancedPatternClick(self):
        if self.advancedPatternFlag:
            self.advancedPatternFlag=False
            self.removePatternOptions()
        else:
            self.advancedPatternFlag=True
            self.removeKeyboard()
            if self.testKeyboardFlag:
                self.testKeyboardFlag=not self.testKeyboardFlag
            self.removeMelodyOptions()
            if self.melodyButtonFlag:
                self.melodyButtonFlag=not self.melodyButtonFlag
			
            #self.removeMelodyOptions()
            #if self.melodyButtonFlag:
            #    self.melodyButtonFlag=not self.melodyButtonFlag
			
            self.setArpeggio.grid(row=13,column=23)
            self.setArpeggio0.grid(row=13,column=7)
            self.setArpeggio1.grid(row=13,column=8)
            self.setArpeggio2.grid(row=13,column=9)
            self.setArpeggio3.grid(row=13,column=10)
            self.setArpeggio4.grid(row=13,column=11)
            self.setArpeggio5.grid(row=13,column=12)
            self.setArpeggio6.grid(row=13,column=13)
            self.setArpeggio7.grid(row=13,column=14)
            self.setArpeggio8.grid(row=13,column=15)
            self.setArpeggio9.grid(row=13,column=16)
            self.setArpeggio10.grid(row=13,column=17)
            self.setArpeggio11.grid(row=13,column=18)
            self.setArpeggio12.grid(row=13,column=19)
            self.setArpeggio13.grid(row=13,column=20)
            self.setArpeggio14.grid(row=13,column=21)
            self.setArpeggio15.grid(row=13,column=22)
			
            self.setBass.grid(row=12,column=23)
            self.setBass0.grid(row=12,column=7)
            self.setBass1.grid(row=12,column=8)
            self.setBass2.grid(row=12,column=9)
            self.setBass3.grid(row=12,column=10)
            self.setBass4.grid(row=12,column=11)
            self.setBass5.grid(row=12,column=12)
            self.setBass6.grid(row=12,column=13)
            self.setBass7.grid(row=12,column=14)
            self.setBass8.grid(row=12,column=15)
            self.setBass9.grid(row=12,column=16)
            self.setBass10.grid(row=12,column=17)
            self.setBass11.grid(row=12,column=18)
            self.setBass12.grid(row=12,column=19)
            self.setBass13.grid(row=12,column=20)
            self.setBass14.grid(row=12,column=21)
            self.setBass15.grid(row=12,column=22)

            self.setChords.grid(row=11,column=15)
            self.setChord0.grid(row=11,column=7)
            self.setChord1.grid(row=11,column=8)
            self.setChord2.grid(row=11,column=9)
            self.setChord3.grid(row=11,column=10)
            self.setChord4.grid(row=11,column=11)
            self.setChord5.grid(row=11,column=12)
            self.setChord6.grid(row=11,column=13)
            self.setChord7.grid(row=11,column=14)
			
            #self.changeKeyButton.grid(row=1,column=6, sticky= "w")
            self.spacePattern.grid(row=1, column=50)
            self.setProgressionText.grid(row=11, column=6)
            self.setArpeggioText.grid(row=13, column=6)
            self.setBassText.grid(row=12, column=6)

    def removeKeyboard(self):
            self.C5.grid_remove()
            self.Db5.grid_remove()
            self.D5.grid_remove()
            self.Eb5.grid_remove()
            self.E5.grid_remove()
            self.F5.grid_remove()
            self.Gb5.grid_remove()
            self.G5.grid_remove()
            self.Ab5.grid_remove()
            self.A5.grid_remove()
            self.Bb5.grid_remove()
            self.B5.grid_remove()
		
            self.C4.grid_remove()
            self.Db4.grid_remove()
            self.D4.grid_remove()
            self.Eb4.grid_remove()
            self.E4.grid_remove()
            self.F4.grid_remove()
            self.Gb4.grid_remove()
            self.G4.grid_remove()
            self.Ab4.grid_remove()
            self.A4.grid_remove()
            self.Bb4.grid_remove()
            self.B4.grid_remove()
			
            self.C3.grid_remove()
            self.Db3.grid_remove()
            self.D3.grid_remove()
            self.Eb3.grid_remove()
            self.E3.grid_remove()
            self.F3.grid_remove()
            self.Gb3.grid_remove()
            self.G3.grid_remove()
            self.Ab3.grid_remove()
            self.A3.grid_remove()
            self.Bb3.grid_remove()
            self.B3.grid_remove()
			
            self.C2.grid_remove()
            self.Db2.grid_remove()
            self.D2.grid_remove()
            self.Eb2.grid_remove()
            self.E2.grid_remove()
            self.F2.grid_remove()
            self.Gb2.grid_remove()
            self.G2.grid_remove()
            self.Ab2.grid_remove()
            self.A2.grid_remove()
            self.Bb2.grid_remove()
            self.B2.grid_remove()
			
            self.CM.grid_remove()
            self.DbM.grid_remove()
            self.DM.grid_remove()
            self.EbM.grid_remove()
            self.EM.grid_remove()
            self.FM.grid_remove()
            self.GbM.grid_remove()
            self.GM.grid_remove()
            self.AbM.grid_remove()
            self.AM.grid_remove()
            self.BbM.grid_remove()
            self.BM.grid_remove()
			
            self.Cm.grid_remove()
            self.Dbm.grid_remove()
            self.Dm.grid_remove()
            self.Ebm.grid_remove()
            self.Em.grid_remove()
            self.Fm.grid_remove()
            self.Gbm.grid_remove()
            self.Gm.grid_remove()
            self.Abm.grid_remove()
            self.Am.grid_remove()
            self.Bbm.grid_remove()
            self.Bm.grid_remove()
			
            self.Cdim.grid_remove()
            self.Dbdim.grid_remove()
            self.Ddim.grid_remove()
            self.Ebdim.grid_remove()
            self.Edim.grid_remove()
            self.Fdim.grid_remove()
            self.Gbdim.grid_remove()
            self.Gdim.grid_remove()
            self.Abdim.grid_remove()
            self.Adim.grid_remove()
            self.Bbdim.grid_remove()
            self.Bdim.grid_remove()
            self.spaceTestKeyboard.grid_remove()
			
    def removeMelodyOptions(self):
            self.melodicDisonanceModeCheck.grid_remove()
            self.periodicChangeCheck.grid_remove()
            self.waitForChangesCheck.grid_remove()
            self.dissonanceInfLimitText.grid_remove()
            self.dissonanceSupLimitText.grid_remove()
            self.dissonanceInfLimitScale.grid_remove()
            self.dissonanceSupLimitScale.grid_remove()
            self.outOfChordScaleText.grid_remove()
            self.outOfChordScale.grid_remove()

    def removePatternOptions(self):
            self.setArpeggio.grid_remove()
            self.setArpeggio0.grid_remove()
            self.setArpeggio1.grid_remove()
            self.setArpeggio2.grid_remove()
            self.setArpeggio3.grid_remove()
            self.setArpeggio4.grid_remove()
            self.setArpeggio5.grid_remove()
            self.setArpeggio6.grid_remove()
            self.setArpeggio7.grid_remove()
            self.setArpeggio8.grid_remove()
            self.setArpeggio9.grid_remove()
            self.setArpeggio10.grid_remove()
            self.setArpeggio11.grid_remove()
            self.setArpeggio12.grid_remove()
            self.setArpeggio13.grid_remove()
            self.setArpeggio14.grid_remove()
            self.setArpeggio15.grid_remove()
			
            self.setBass.grid_remove()
            self.setBass0.grid_remove()
            self.setBass1.grid_remove()
            self.setBass2.grid_remove()
            self.setBass3.grid_remove()
            self.setBass4.grid_remove()
            self.setBass5.grid_remove()
            self.setBass6.grid_remove()
            self.setBass7.grid_remove()
            self.setBass8.grid_remove()
            self.setBass9.grid_remove()
            self.setBass10.grid_remove()
            self.setBass11.grid_remove()
            self.setBass12.grid_remove()
            self.setBass13.grid_remove()
            self.setBass14.grid_remove()
            self.setBass15.grid_remove()
			
            self.setChords.grid_remove()
            self.setChord0.grid_remove()
            self.setChord1.grid_remove()
            self.setChord2.grid_remove()
            self.setChord3.grid_remove()
            self.setChord4.grid_remove()
            self.setChord5.grid_remove()
            self.setChord6.grid_remove()
            self.setChord7.grid_remove()
			
            #self.changeKeyButton.grid_remove()
            self.spacePattern.grid_remove()
            self.setProgressionText.grid_remove()
            self.setArpeggioText.grid_remove()
            self.setBassText.grid_remove()
			
    def onChangeChordsClick(self):
        self.changeChordsFlag=True #Wait for current progression before doing anything!
        print "Changing chord progression in next section"
		
    def onChangeArpeggioClick(self):
        self.changeArpeggioFlag=True
		
    def onChangeBassClick(self):
        self.changeBassFlag=True 
	
    def onChangeKeyClick(self):
        self.changeKeyFlag=True #Wait for current progression before doing anything!
        print "Changing Key, chords and scale on next section"
		
    def onSetArpeggioClick(self,pos):#,octave):
        #self.userArpeggio[pos]=[pos,note,"3"]
        self.userArpeggio[pos]=self.userArpeggio[pos]+1
        if self.userArpeggio[pos]>2:
            self.userArpeggio[pos]=-1

        if pos==0: #There should be a better way...
            self.setArpeggio0.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==1:
            self.setArpeggio1.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==2:
            self.setArpeggio2.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==3:
            self.setArpeggio3.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==4:
            self.setArpeggio4.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==5:
            self.setArpeggio5.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==6:
            self.setArpeggio6.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==7:
            self.setArpeggio7.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==8:
            self.setArpeggio8.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==9:
            self.setArpeggio9.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==10:
            self.setArpeggio10.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==11:
            self.setArpeggio11.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==12:
            self.setArpeggio12.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==13:
            self.setArpeggio13.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==14:
            self.setArpeggio14.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )
        if pos==15:
            self.setArpeggio15.config(text=self.patternShow[self.userArpeggio[pos]+1], command=lambda: self.onSetArpeggioClick(pos) )

    def onSetArpeggioApplyClick(self,compassBeats,arpeggio):
        pattern=[]
        for i in range(0,self.compassBeats):
            if arpeggio[i]>-1:
                #if arpeggio[i]>2:  # Maybe clever way: octave= 3+floor(arpeggio[i]/3)
				    #if arpeggio[i]<6:
      				    # arpeggio[i]=arpeggio[i]-3
					    # octave="4"
					#else:
					    # arpeggio[i]=arpeggio[i]-6
					    # octave="4"
                pattern.append([i,arpeggio[i],"3"]) #Only notes from 3th octave...			
        self.arpeggioPattern=pattern
        print "User arpeggio Set"
        return pattern
	
    def onSetBassClick(self,pos):#,octave):
        #self.userArpeggio[pos]=[pos,note,"3"]
        self.userBass[pos]=self.userBass[pos]+1
        if self.userBass[pos]>2:
            self.userBass[pos]=-1

        if pos==0: #There should be a better way...
            self.setBass0.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==1:
            self.setBass1.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==2:
            self.setBass2.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==3:
            self.setBass3.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==4:
            self.setBass4.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==5:
            self.setBass5.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==6:
            self.setBass6.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==7:
            self.setBass7.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==8:
            self.setBass8.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==9:
            self.setBass9.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==10:
            self.setBass10.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==11:
            self.setBass11.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==12:
            self.setBass12.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==13:
            self.setBass13.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==14:
            self.setBass14.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )
        if pos==15:
            self.setBass15.config(text=self.patternShow[self.userBass[pos]+1], command=lambda: self.onSetBassClick(pos) )

    def onSetBassApplyClick(self,compassBeats,bass):
        pattern=[]
        for i in range(0,self.compassBeats):
            if bass[i]>-1:
                pattern.append([i,bass[i],"2"]) #Only notes from 2nd octave...			
        self.bassPattern=pattern
        print "User bass Set"
        return pattern
	
    def onSetChordClick(self,pos,mode):
        self.userChords[pos]=self.userChords[pos]+1
        if mode=="major":
            self.chordsShow=list(self.chordsMajorShow)
            chordsEnd=7
        else:
            self.chordsShow=list(self.chordsMinorShow)
            chordsEnd=8
        if self.userChords[pos]>(chordsEnd):
            self.userChords[pos]=0
		

        if pos==0: #There should be a better way...
            self.setChord0.config(text=self.chordsShow[self.userChords[pos]], command=lambda: self.onSetChordClick(pos,self.mode) )
        if pos==1:
            self.setChord1.config(text=self.chordsShow[self.userChords[pos]], command=lambda: self.onSetChordClick(pos,self.mode) )
        if pos==2:
            self.setChord2.config(text=self.chordsShow[self.userChords[pos]], command=lambda: self.onSetChordClick(pos,self.mode) )
        if pos==3:
            self.setChord3.config(text=self.chordsShow[self.userChords[pos]], command=lambda: self.onSetChordClick(pos,self.mode) )
        if pos==4:
            self.setChord4.config(text=self.chordsShow[self.userChords[pos]], command=lambda: self.onSetChordClick(pos,self.mode) )
        if pos==5:
            self.setChord5.config(text=self.chordsShow[self.userChords[pos]], command=lambda: self.onSetChordClick(pos,self.mode) )
        if pos==6:
            self.setChord6.config(text=self.chordsShow[self.userChords[pos]], command=lambda: self.onSetChordClick(pos,self.mode) )
        if pos==7:
            self.setChord7.config(text=self.chordsShow[self.userChords[pos]], command=lambda: self.onSetChordClick(pos,self.mode) )

    def onSetChordsApplyClick(self):
        print "Setting user progression on next cycle"
        self.userSetProgressionFlag=True
####################</GUI>####################

####################<NOTE>####################
def winPlay(note):
    winsound.PlaySound(note,winsound.SND_FILENAME)
####################</NOTE>####################

if __name__=='__main__':
    freeze_support()
    print("Composing\n")
    pythozart=Pythozart()
    print("Closing\n")