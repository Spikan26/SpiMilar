import tkinter as tk
from PIL import Image, ImageTk
from io import BytesIO
import vlc
import websocket as wsapp
import requests
from yt_dlp import YoutubeDL
import config

# Global Variable
playState = False
firstPlay = True
is_loop = False

##################### VLC #####################

class VLC:

    def __init__(self):
        self.volumelevel = 50
        self.currentTitle = ""
        self.yt_url = ""
        self.audio_link = ""
        self.currentDuration = 0
        self.mediaPlayer = vlc.MediaPlayer('--loop')
        self.mediaPlayer.audio_set_volume(50)
        self.queuelist = []
    
    def GetSimilarSong(self, songURL):
        # Search for Track
        r_search_track = requests.get(url=config.CHOSIC_SEARCH_TRACK+songURL+"&type=track&limit=5", headers=config.CHOSIC_HEADER)
        input_song_id = r_search_track.json()["tracks"]["items"][0]["id"]
        input_song_name = r_search_track.json()["tracks"]["items"][0]["name"]
        input_song_artist = r_search_track.json()["tracks"]["items"][0]["artist"]
        input_song_image = r_search_track.json()["tracks"]["items"][0]["image"]
        
        response = requests.get(input_song_image)
        image_src= Image.open(BytesIO(response.content))
        resize_img = image_src.resize((100,100))
        image_album = ImageTk.PhotoImage(resize_img)
        app.inputSongImage.config(image=image_album)
        app.inputSongImage.image = image_album

        r_get_similar = requests.get(url=config.CHOSIC_GET_SIMILAR+input_song_id+"&limit=100", headers=config.CHOSIC_HEADER)
        for item in r_get_similar.json()["tracks"]:
            self.queuelist.append(item)

    def GetSimilarSongURL(self, songURL):
        with YoutubeDL({'ignoreerrors': True, 'quiet': True, 'extract_flat': False}) as ydl:
            video_info = ydl.extract_info(
                songURL, download=False)

            try:
                input_song_title = video_info['title']

                # Search for Track
                r_search_track = requests.get(url=config.CHOSIC_SEARCH_TRACK+input_song_title+"&type=track&limit=5", headers=config.CHOSIC_HEADER)
                input_song_id = r_search_track.json()["tracks"]["items"][0]["id"]
                input_song_name = r_search_track.json()["tracks"]["items"][0]["name"]
                input_song_artist = r_search_track.json()["tracks"]["items"][0]["artist"]

                r_get_similar = requests.get(url=config.CHOSIC_GET_SIMILAR+input_song_id+"&limit=100", headers=config.CHOSIC_HEADER)
                for item in r_get_similar.json()["tracks"]:
                    self.queuelist.append(item)

            except:
                print("Video is private or unavailable")

    def addFromQueuelist(self):
        # (link, title, user)
        obj_request = self.queuelist.pop(0)

        song_name = obj_request['name']
        song_artist = obj_request['artists'][0]['name']
        song_image = obj_request['album']['image_large']

        response = requests.get(song_image)
        image_src= Image.open(BytesIO(response.content))
        resize_img = image_src.resize((100, 100))
        image_album = ImageTk.PhotoImage(resize_img)
        app.outputSongImage.config(image=image_album)
        app.outputSongImage.image = image_album

        r_get_video_song = requests.get(url=config.CHOSIC_GET_VIDEO_SONG+"?song="+song_name+"&artist="+song_artist, headers=config.CHOSIC_HEADER)
        song_url = r_get_video_song.text.replace("\"","")    #.decode('utf8')


        with YoutubeDL({'ignoreerrors': True, 'quiet': True}) as ydl:
            video_info = ydl.extract_info(
                "https://www.youtube.com/watch?v="+str(song_url), download=False)
            url_yt = ""
            for i, format in enumerate(video_info['formats']):
                try:
                    url_yt = format['audio_channels']
                    url_yt = format['url']
                    self.yt_url = "www.youtube.com/watch?v=" + \
                        video_info['id']
                    self.currentTitle = video_info['title']
                    self.currentDuration = video_info['duration']
                    break
                except:
                    pass
            
            self.audio_link = url_yt
            self.mediaPlayer.set_mrl(url_yt, ":no-video")
            self.mediaPlayer.play()

    def updateTitle(self):
        global app
        app.current_play.config(text=str(self.currentTitle))
        with open('current_title_source.txt', 'w', encoding='utf-8') as f:
            f.write(str(self.currentTitle)+" - ")
        print(self.currentTitle)

    def play(self):
        global playState
        global firstPlay

        if(firstPlay):
            firstPlay = False

        if (playState):
            self.mediaPlayer.pause()
            playState = False
            return

        playState = True
        self.mediaPlayer.play()

    def next(self):
        self.mediaPlayer.stop()
        self.mediaPlayer = vlc.MediaPlayer('--loop')
        if len(self.queuelist) > 0:
            self.addFromQueuelist()
        self.event_vlc()
        self.updateTitle()

    def pause(self):
        self.mediaPlayer.pause()

    def stop(self):
        global playState

        playState = False
        self.mediaPlayer.stop()

    def volume(self):
        self.mediaPlayer.audio_set_volume(int(self.volumelevel))

    def event_vlc(self):
        # Event for media stop
        self.mediaPlayer.event_manager().event_attach(
            vlc.EventType.MediaPlayerEndReached, self.media_player_on, 1)

    def media_player_on(self, event, arg):
        global is_loop
        print("Music ended")
        self.mediaPlayer = vlc.MediaPlayer('--loop')
        if is_loop:
            self.mediaPlayer.stop()
            self.mediaPlayer.set_mrl(self.audio_link, ":no-video")
            self.mediaPlayer.play()
        elif len(self.queuelist) > 0:
            self.addFromQueuelist()
        self.event_vlc()
        self.updateTitle()

    def add_favorite(self):
        with open('favorite.txt', 'a', encoding='utf-8') as f:
            f.write(str(self.currentTitle)+' - '+str(self.yt_url)+'\n')

    def looping(self):
        global is_loop
        if is_loop:
            is_loop = False
            app.loop_button.configure(background="#f0f0f0")
        else:
            is_loop = True
            app.loop_button.configure(background="#9ccfff")

    def test(self):
        # songURL = config.SONG_URL
        # self.GetSimilarSongURL(songURL)
        self.queuelist = []
        songURL = app.userInputSong.get()
        self.GetSimilarSong(songURL)
        self.addFromQueuelist()
        self.event_vlc()
        self.updateTitle()


##################### Tkinter #####################

class SpiMusik:
    def __init__(self):
        global player
        # Create a new window
        self.root = tk.Tk()

        # Set the title of the window
        self.root.title("SpiMilar")

        # Set the size of the window
        self.root.geometry("600x400")

        # Create a function to handle slider updates
        self.titlePlayingBox = tk.Frame(self.root, name="currentplay")
        self.controlBox = tk.Frame(self.root, name="volume")
        self.controlBtnBox = tk.Frame(self.root, name="bouton")
        self.playerProgress = tk.Frame(self.root, name="progress")
        self.inputSongBox = tk.Frame(self.root, name="inputsong")
        self.infoBox = tk.Frame(self.root, name="info")
        self.infoInput = tk.Frame(self.infoBox, name="infoInput")
        self.infoOutput = tk.Frame(self.infoBox, name="infoOuput")
        

        # Create a label for the slider
        self.current_play = tk.Label(
            self.titlePlayingBox, name="current_play", text="...", background="light blue")
        self.current_play.grid(column=0, row=0)

        self.titlePlayingBox.pack()

        # Create a label for the slider
        self.volume_label = tk.Label(
            self.controlBox, name="volume_label", text="Volume: 0")
        self.volume_label.grid(column=1, row=1)

        # Create a slider
        self.volume_slider = tk.Scale(self.controlBox, name="volume_slider", from_=0, to=100, orient=tk.HORIZONTAL, length=200,
                                      command=lambda value: self.slider_update(value))
        self.volume_slider.grid(column=2, row=1)

        self.controlBox.pack()

        # Create buttons
        self.play_button = tk.Button(self.controlBtnBox, name="play_button", text="Play",
                                     command=lambda: player.play())
        self.play_button.grid(column=0, row=2)

        self.stop_button = tk.Button(self.controlBtnBox, name="stop_button", text="Stop",
                                     command=lambda: player.stop())
        self.stop_button.grid(column=1, row=2)

        self.next_button = tk.Button(self.controlBtnBox, name="next_button", text="Next",
                                     command=lambda: player.next())
        self.next_button.grid(column=2, row=2)

        self.loop_button = tk.Button(self.controlBtnBox, name="loop_button", text="Loop",
                                     command=lambda: player.looping())
        self.loop_button.grid(column=3, row=2)

        # self.test_button = tk.Button(self.controlBtnBox, name="test_button", text="TEST",
        #                              command=lambda: player.test())
        # self.test_button.grid(column=3, row=2)

        self.favorite_button = tk.Button(self.controlBtnBox, name="favorite_button", text="Favorite",
                                         command=lambda: player.add_favorite())
        self.favorite_button.grid(column=4, row=2)

        
        self.controlBtnBox.pack()

        self.player_progress = tk.Label(
            self.playerProgress, name="player_progress", text="0:00 / 0:00")
        self.player_progress.grid(column=0, row=0)

        self.playerProgress.pack()


        self.userInputSong = tk.Entry(self.inputSongBox)
        self.userInputSong.grid(column=0, row=0)

        self.test_button = tk.Button(self.inputSongBox, name="test_button", text="TEST",
                                     command=lambda: player.test())
        self.test_button.grid(column=1, row=0)

        self.inputSongBox.pack()

        self.inputSongImage = tk.Label(self.infoInput)
        self.inputSongImage.grid(column=0, row=0)
        
        self.outputSongImage = tk.Label(self.infoOutput)
        self.outputSongImage.grid(column=1, row=0)

        self.infoInput.grid(column=0, row=0)
        self.infoOutput.grid(column=1, row=0)
        self.infoBox.pack()

    def slider_update(self, value):
        self.volume_label.config(text=f"Volume: {value}")
        player.volumelevel = value
        player.volume()

    def current_player_time(self):
        current_time_min = (player.mediaPlayer.get_time() // 1000) // 60
        current_time_sec = (player.mediaPlayer.get_time() // 1000) % 60
        total_time_min = player.currentDuration // 60
        total_time_sec = player.currentDuration % 60

        actual_time = f"{current_time_min:02d}:{current_time_sec:02d} / {total_time_min:02d}:{total_time_sec:02d}"
        self.player_progress.config(text=actual_time)
        self.root.after(1000, self.current_player_time)


############################################################################################################

player = VLC()
app = SpiMusik()
# Run the window
app.root.after(1000, player.updateTitle())
app.root.after(2000, app.current_player_time())
app.root.mainloop()
