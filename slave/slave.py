import Tkinter
import sys
import Pyro4
import psutil
import multiprocessing
import time
import pyscreenshot
import base64

import generated_vlc as vlc

def stream_player_error(player, *args, **kwargs):
    print(args)
    print(kwargs)
    player.stop()

def stream_player_process(pipe, stream_url):
    instance = vlc.Instance()
    try:
        media = instance.media_new(stream_url)
    except NameError:
        print('NameError: %s (%s vs LibVLC %s)' % (sys.exc_info()[1],
                                                   vlc.__version__,
                                                   vlc.libvlc_get_version()))
        return

    player = instance.media_player_new()

    event_manager = player.event_manager()
    event_manager.event_attach(vlc.EventType.MediaPlayerEncounteredError, stream_player_error, player)

    player.set_media(media)
    player.play()
    player.set_fullscreen(True)

    # Give VLC a bit to start playing the stream
    time.sleep(3)

    while True:
        cmd = ""
        if pipe.poll(1):
            cmd = pipe.recv()
            if cmd == "stop":
                break

        if not player.is_playing() or not player.has_vout():
            break

        time.sleep(1)

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
