import pygame
from cfg_var import *

#from pydub import AudioSegment  # for def readMp3File2
#import simpleaudio as sa        # for def readMp3File2
#from subprocess import call     # for def readMp3File3

music_file = "music.mp3"

freq = 16000    # sampling rate, 44100(CD), 16000(Naver TTS), 24000(google TTS)
bitsize = -16   # signed 16 bit. support 8,-8,16,-16
channels = 1    # 1 is mono, 2 is stereo
buffer = 2048   # number of samples (experiment to get right sound)


def readMp3File():
    # default : pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=4096)
    pygame.mixer.init(freq, bitsize, channels, buffer)
    pygame.mixer.music.load(music_file)
    pygame.mixer.music.play()

    clock = pygame.time.Clock()
    while pygame.mixer.music.get_busy():
        clock.tick(30)
    pygame.mixer.quit()


def readMp3File2():     # translate mp3 to wav and play
    song = AudioSegment.from_mp3('music.mp3')
    song.export('music.wav', format = 'wav')

    music = sa.WaveObject.from_wave_file(cfg_MAIN_DIR + '/music.wav')
    play = music.play()
    play.wait_done()


def readMp3File3():     # play mp3 via shell command
    call('mpg123 -vC music.mp3', shell = True)


if __name__ == "__main__":
    readMp3File()