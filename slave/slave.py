import Tkinter
import sys
import Pyro4
import psutil
import multiprocessing
import time
import pyscreenshot
import base64
import ctypes
import logging
from functools import partial

import generated_vlc as vlc


def bytes_to_str(b):
    if isinstance(b, str):
        return unicode(b, sys.getfilesystemencoding())
    else:
        return b

def mspf(player):
    """Milliseconds per frame."""
    return int(1000 // (player.get_fps() or 25))

def stream_player_error(event, player):
    print(event)

    media = player.get_media()
    print('State: %s' % player.get_state())
    print('Media: %s' % bytes_to_str(media.get_mrl()))
    print('Track: %s/%s' % (player.video_get_track(), player.video_get_track_count()))
    print('Current time: %s/%s' % (player.get_time(), media.get_duration()))
    print('Position: %s' % player.get_position())
    print('FPS: %s (%d ms)' % (player.get_fps(), mspf(player)))
    print('Rate: %s' % player.get_rate())
    print('Video size: %s' % str(player.video_get_size(0)))  # num=0
    print('Scale: %s' % player.video_get_scale())
    print('Aspect ratio: %s' % player.video_get_aspect_ratio())
    #print('Window:' % player.get_hwnd()

    #player.stop()


class VLCLogHandler:
    libc = ctypes.CDLL("libc.so.6")

    @vlc.CallbackDecorators.LogCb
    def log_handler(instance, log_level, log, fmt, va_list):
        bufferString = ctypes.create_string_buffer(4096)
        VLCLogHandler.libc.vsprintf(bufferString, fmt, ctypes.cast(va_list, ctypes.c_void_p))
        logging.warn(bufferString.raw)


def stream_player_process(pipe, stream_url):
    instance = vlc.Instance()

    try:
        # Create new media from stream URL
        media = instance.media_new(stream_url)
    except NameError:
        print('NameError: %s (%s vs LibVLC %s)' % (sys.exc_info()[1],
                                                   vlc.__version__,
                                                   vlc.libvlc_get_version()))
        return

    player = instance.media_player_new()

    instance.log_set(VLCLogHandler.log_handler, player)

    event_manager = player.event_manager()
    event_manager.event_attach(vlc.EventType.MediaPlayerEncounteredError, stream_player_error, player)

    player.set_media(media)

    # To play YouTube stream URLs (besides everything else)
    # we have to create a media_list and a media_list_player
    # Otherwise libvlc won't resolve a YT URL to a real stream URL
    media_list = instance.media_list_new([media])

    list_player = instance.media_list_player_new()
    list_player.set_media_player(player)
    list_player.set_media_list(media_list)

    list_player.play()

    player.set_fullscreen(True)

    # Give VLC a bit to start playing the stream
    time.sleep(3)

    while True:
        cmd = ""
        if pipe.poll(1):
            cmd = pipe.recv()
            if cmd == "stop":
                break

        if not player.is_playing():
            break

        time.sleep(1)

    media.release()
    media_list.release()
    list_player.release()
    player.release()

    pipe.close()


class StreamSlaveControl:
    def __init__(self):
        self.stream_player = None
        self.stream_player_pipe = None
        self.stream_url = None

    def get_system_status(self):
        return {
            "load": psutil.cpu_percent(),
            "mem_used": psutil.virtual_memory().percent,
        }

    def start_stream(self, stream_url):
        if self.stream_player:
            if self.stream_player.is_alive():
                self.stop_stream()
            else:
                self.stream_player_pipe.close()

        self.stream_url = stream_url
        (self.stream_player_pipe, process_pipe) = multiprocessing.Pipe(duplex=True)
        self.stream_player = multiprocessing.Process(target=stream_player_process, args=(process_pipe, stream_url))
        self.stream_player.start()

    def stop_stream(self):
        if self.stream_player_pipe:
            self.stream_player_pipe.send("stop")
            self.stream_player_pipe.close()

    def get_screenshot(self):
        img = pyscreenshot.grab()
        img.thumbnail((200, 200))
        return {"data": base64.b64encode(img.tobytes()), "size": img.size, "mode": img.mode}

    def get_status(self):
        if not self.stream_player:
            return 'Idle'

        if self.stream_player.is_alive():
            return 'Playing stream'
        else:
            return 'Stream stopped'


def generate_free_name(ns):
    registered_slaves = ns.list(prefix="slave")

    max_num = 0
    for slave, _ in registered_slaves.items():
        num = int(slave.split(".")[1])

        if num > max_num:
            max_num = num

    max_num += 1

    return "slave.%d" % (max_num)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--test":
        ss = StreamSlaveControl()
        #ss.start_stream("/home/fabian/20140731-TVGE2110-Monty_Python_live__mostly_.mp4")
        ss.start_stream("https://youtu.be/ikpc1BN4nN8")
        sys.exit(0)

    daemon = Pyro4.Daemon()
    print("Locating nameserver ...")
    ns = Pyro4.locateNS()
    uri = daemon.register(StreamSlaveControl())

    if len(sys.argv) == 2:
        name = "slave.%s" % (sys.argv[1])
    else:
        name = generate_free_name(ns)

    print("Registering with nameserver (name: %s) ..." % (name))
    ns.register(name, uri, safe=True)

    print("Done! Starting event loop ...")
    daemon.requestLoop()

    print("Removing ourself from the name server ...")
    ns.remove(name)
    print("Good bye!")
