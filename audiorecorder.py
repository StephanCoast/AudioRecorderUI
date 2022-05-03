#!/usr/bin/python
# ‐*‐ encoding: utf‐8 ‐*‐

import datetime
import shutil
import time
import tkinter
import urllib.request
import urllib.error
from os.path import exists
from tkinter import messagebox
from docopt import docopt
import os
from tkinter import *
import threading
import vlc
import validators

__author__ = "Stephan Kost"
__version__ = "0.1"

__doc__ = \
    """AudioRecorder

    Usage:
      audiorecorder.py [<url>] [--filename=<name>] [--duration=<time>] [--blocksize=<size>]
      audiorecorder.py -h | --help
      audiorecorder.py -l | --listrecordings
      audiorecorder.py -u | --ui
      
    
    Options:
      -h --help             Show this screen.
      -u --ui               Run audio recorder with UI.
      -l --listrecordings   List all recordings in audiorecorder folder
      --url=<url>           Source URL of radio stream
      --filename=<name>     Name of recording [default: myRadio.mp3]
      --duration=<time>     Duration of recording in seconds [default: 10]
      --blocksize=<size>    Block size for read/write in bytes [default: 128]
    """


def print_recordings():
    print("Previous Recordings: ")
    print([f for f in os.listdir(os.getcwd()) if f.endswith('.mp3')])


class Audiorecorder:
    """
    Audiorecorder Class
    """

    def __init__(self, url, filename, duration, blocksize):
        self.b1 = self.b2 = self.b3 = self.b4 = self.b5 = self.b6 = None
        self.url = url
        self.temp_filename = None
        self.filename = filename
        self.duration = duration
        self.blocksize = blocksize
        self.t = None
        self.rec_done = FALSE
        self.player = None
        self.stopped = self.closed = FALSE
        self.saved = FALSE

        # TKinter UI
        self.root = Tk()
        self.root.title('Audiorecorder v' + __version__)
        self.root.geometry("400x180")
        # UI - Buttons & Formentries
        self.record_img = PhotoImage(file="png/glyphicons-170-record.png", master=self.root)
        self.play_img = PhotoImage(file="png/glyphicons-174-play.png", master=self.root)
        self.pause_img = PhotoImage(file="png/glyphicons-175-pause.png", master=self.root)
        self.stop_img = PhotoImage(file="png/glyphicons-176-stop.png", master=self.root)
        self.save_img = PhotoImage(file="png/glyphicons-447-floppy-save.png", master=self.root)
        self.bt_size = 20
        self.padding = 5
        self.fields = ('Source-URL', 'Filename', 'Duration (s)', 'Blocksize')
        self.entries = self.makeform()
        self.entries['Source-URL'].insert(0, self.url)
        self.entries['Filename'].insert(0, self.filename)
        self.entries['Duration (s)'].insert(0, self.duration)
        self.entries['Blocksize'].insert(0, self.blocksize)

        if args['<url>'] is None:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()

    # UI Event Methods
    def exit_pressed(self):
        # delete temporary file on exit
        if not self.saved and self.temp_filename:
            if messagebox.askokcancel("Quit", "Do you want to quit? Unsaved file will be lost."):
                self.close()
        else:
            self.close()

    def close(self):
        self.root.withdraw()
        self.stopped = self.closed = TRUE
        if self.player:
            self.player.release()
        print(threading.enumerate())
        if self.temp_filename:
            os.remove(self.temp_filename)
        self.root.destroy()

    def on_closing(self):
        self.exit_pressed()

    def record_pressed(self):
        if not self.t:
            self.stopped = FALSE
            self.t = threading.Thread(target=self.long_running_task)
            self.t.start()
            print(threading.enumerate())
        else:
            Audiorecorder('http://radios.rtbf.be/vivabxl-128.mp3', self.filename, 10, self.blocksize)

    def long_running_task(self):
        self.entries['Source-URL']['state'] = self.entries['Duration (s)']['state'] = self.entries['Blocksize'][
            'state'] = 'disabled'
        self.record_stream()
        # Clean up temp file or load temp file into player after thread finished
        if self.rec_done == TRUE:
            if self.closed == TRUE:
                os.remove(self.temp_filename)
            else:
                # Update Player
                self.player = vlc.MediaPlayer(self.temp_filename)  # load last recorded in Player
                self.b2['state'] = self.b3['state'] = self.b4['state'] = self.b5['state'] = NORMAL
                # Write Back actual recording times
                self.entries['Duration (s)']['state'] = NORMAL
                self.entries['Duration (s)'].delete(0, END)
                self.entries['Duration (s)'].insert(0, self.duration)
                self.entries['Duration (s)']['state'] = DISABLED
                print("Duration: " + str(self.duration))

    def play_pressed(self):
        if self.player.is_playing() == 0:
            self.player.stop()
            self.player.play()

    def pause_pressed(self):
        self.player.pause()

    def stop_pressed(self):
        if self.t and self.t.is_alive():
            self.stopped = TRUE
            print("stopped recording: ", self.stopped)
            self.player = vlc.MediaPlayer(self.temp_filename)  # load last recorded in Player
            self.b2['state'] = self.b3['state'] = self.b5['state'] = NORMAL

        elif self.player:
            self.player.stop()

    def save_pressed(self):
        if self.saved == FALSE:
            try:
                self.filename = self.entries['Filename'].get()
                # Form Validation
                if self.filename[-4:] != ".mp3":  # Make sure filename ends with <.mp3>
                    self.filename += ".mp3"
                    self.entries['Filename'].delete(0, END)
                    self.entries['Filename'].insert(0, self.filename)
                if exists(self.filename):
                    if messagebox.askokcancel("Overwrite existing file?",
                                              "Do you want to overwrite the existing file with the same name?"):
                        shutil.copyfile(self.temp_filename, self.filename)
                else:
                    shutil.copyfile(self.temp_filename, self.filename)

                self.saved = TRUE

            except PermissionError as e:
                print("Error:", e)
                tkinter.messagebox.showerror('Permission Error',
                                             'The file is currently in use, please choose a different file name!')

    def record_stream(self):
        try:
            if validators.url(self.entries['Source-URL'].get()):
                self.url = self.entries['Source-URL'].get()
            else:
                self.entries['Source-URL'].delete(0, END)
                self.entries['Source-URL'].insert(0, "Please enter valid URL!")

            if not self.entries['Duration (s)'].get().isnumeric():
                self.entries['Duration (s)'].delete(0, END)
                self.entries['Duration (s)'].insert(0, "Please enter integer value!")
            else:
                self.duration = self.entries['Duration (s)'].get()

            if not self.entries['Blocksize'].get().isnumeric():
                self.entries['Blocksize'].delete(0, END)
                self.entries['Blocksize'].insert(0, "Please enter integer value!")
            else:
                self.blocksize = self.entries['Blocksize'].get()

            audio_src = urllib.request.urlopen(self.url)
            start_time = time.time()

            # Unterschied CLI und UI
            if args['<url>'] is None:
                self.temp_filename = "rec" + str(datetime.datetime.now().strftime("%y%m%d%H%M%S")) + ".mp3"
            else:
                self.temp_filename = args['--filename']

            # with open -> Datei wird nach dem Block automatisch geschlossen
            with open(self.temp_filename, 'wb') as audio_dst:
                while (time.time() - start_time) < int(self.duration):
                    if self.stopped == TRUE:
                        break
                    # Puffergröße sorgt für längere Aufnahme, Streams mit möglichst großem Puffer um mangelnde Bandbreite abzufedern
                    audio_dst.write(audio_src.read(int(self.blocksize)))
                self.duration = round(time.time() - start_time + 1.5)

        except urllib.error.URLError as e:
            print("The URL could not be found:", e)
            tkinter.messagebox.showinfo('URL not found', 'The URL could not be found. Please check!')
        except TypeError as e:
            print("Error:", e)
        except ValueError as e:
            print("Error:", e)
        except Exception as e:  # any other Exception
            print("Error:", e, e.__class__)
        except PermissionError:
            print("Exception: No permission to write" + self.filename)
        else:  # no exception occured
            print("No exception occured.")
            print('Recording done')
            self.rec_done = TRUE

    def makeform(self):
        entries = {}
        for field in self.fields:
            row = Frame(self.root)
            lab = Label(row, width=10, text=field + ": ", anchor='w')
            ent = Entry(row)
            row.pack(side=TOP, fill=X, padx=5, pady=5)
            lab.pack(side=LEFT)
            ent.pack(side=RIGHT, expand=YES, fill=X)
            entries[field] = ent

        controlframe = Frame(self.root)
        self.b1 = Button(controlframe, image=self.record_img, command=self.record_pressed, width=self.bt_size,
                         height=self.bt_size)
        self.b1.pack(side=LEFT, padx=self.padding, pady=self.padding)
        self.b2 = Button(controlframe, image=self.play_img, command=self.play_pressed, width=self.bt_size,
                         height=self.bt_size)
        self.b2.pack(side=LEFT, padx=self.padding, pady=self.padding)
        self.b2['state'] = DISABLED
        self.b3 = Button(controlframe, image=self.pause_img, command=self.pause_pressed, width=self.bt_size,
                         height=self.bt_size)
        self.b3.pack(side=LEFT, padx=self.padding, pady=self.padding)
        self.b3['state'] = DISABLED
        self.b4 = Button(controlframe, image=self.stop_img, command=self.stop_pressed, width=self.bt_size,
                         height=self.bt_size)
        self.b4.pack(side=LEFT, padx=self.padding, pady=self.padding)
        # self.b4['state'] = DISABLED
        self.b5 = Button(controlframe, image=self.save_img, command=self.save_pressed, width=self.bt_size,
                         height=self.bt_size)
        self.b5.pack(side=LEFT, padx=self.padding, pady=self.padding)
        self.b5['state'] = DISABLED
        self.b6 = Button(controlframe, text='Exit', command=self.exit_pressed)
        self.b6.pack(side=LEFT, padx=self.padding, pady=self.padding)
        controlframe.pack(side=TOP, fill=X, padx=5, pady=5)

        return entries


if __name__ == '__main__':
    args = docopt(__doc__, version='AudioRecorder 1.0')

    # for pair in args.items():
    # print(pair)

    # Load with UI
    if args['<url>'] is None or args['--ui']:
        print(__doc__)
        audio_recorder = Audiorecorder('http://radios.rtbf.be/vivabxl-128.mp3', args['--filename'], args['--duration'],
                                       args['--blocksize'])

    elif args['--listrecordings']:
        print_recordings()

    elif args['<url>'] is not None:
        if args['--filename'][-4:] != ".mp3":  # Make sure filename ends with <.mp3>
            args['--filename'] += ".mp3"

        audio_recorder = Audiorecorder(args['<url>'], args['--filename'], args['--duration'], args['--blocksize'])
        audio_recorder.record_stream()
    else:
        print("command not found")
