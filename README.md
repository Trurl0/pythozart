# Pythozart
Not-so-random music generator in python

Continuously plays music based in common chord progressions and basic musical structures.
Also prints random poetry at the same time so you have something to read while listening.

Sounds kind of appropiate as elevator music.


## Acknowledgments
Thanks to Nina Aranda for musical consulting, if something doesn't sound right it's my fault for not knowing enough theory nor having the time to learn it :/


## FAQ:
#### ¿What does ... mean?

Key: the key of the song.

Chords: chord progression type.

Scale: scale used, in the tonality defined by Key.

Beats/Bar: maximun number of notes in a single bar.

Tempo: minimun number of seconds between notes

Randomize: randomizes all parameters (some changes won't apply if a song is in progress).

#### ¿Can some parameters be changed during a song?

Yes, most of them, with the exception of key, chords, scale and Beats/bar.

#### ¿Why 5 guitars?

Each one has a different octave range. In addition the "melody" voice is also a guitar (_my guitar_), but with a different logic and a range of three octaves (3-5)

#### ¿Why there is so much noise?

Because I own some cheap mics, I should fire a kickstarter or something.

#### ¿Why do the chords sound so bad?

Same as above.

#### I am getting error messages and is playing out of time, why is that?

Try removing some instruments or slowing the tempo, sometimes the OS can't handle all the play note requests (each one is a short life thread) and they get stuck in the queue. Maybe python is not the best language for this or I am doing something wrong, who knows?

#### ¿There are no more instruments than guitars?

Not for the moment, but is on the list. I'm thinking on adding some violins, but I still have to think about how to handle note lenght

#### ¿Why does the keyboard has delay? 

Because it's not a separate process, but I have no intention to solve it for the moment. It's only for testing, pick your own instrument if you wanna play along (don't forget to record and send it if you wanna make me happy! :] ).

