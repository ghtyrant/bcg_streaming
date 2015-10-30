import sys
import Pyro4
import psutil
import multiprocessing
import time
import base64
import ctypes
import logging
import os
import hashlib
from functools import partial

def running_on_pi():
    return os.uname()[4].startswith("arm")

if running_on_pi():
    import subprocess
    from PIL import Image
else:
    import pyscreenshot
    import generated_vlc as vlc


if running_on_pi():
    OMX_ARGS = ["/usr/bin/omxplayer.bin", "-r", "-o", "local", "-w"]
    def stream_player_process(pipe, stream_url):
        p = subprocess.Popen(OMX_ARGS + [stream_url,], stdin=subprocess.PIPE)
        while True:
            cmd = ""
            if pipe.poll(1):
                cmd = pipe.recv()
                if cmd == "stop":
                    break

            # Restart omxplayer in case it died
            if p.poll() is not None:
                print("Restarting omxplayer ...")
                p = subprocess.Popen(OMX_ARGS + [stream_url,], stdin=subprocess.PIPE)

            time.sleep(1)

        print("Terminating player ...")

        try:
            p.communicate(input=b'q')
        except IOError:
            p.kill()

        p.wait()
        subprocess.call(["/usr/bin/fbset", "-depth", "8"])
        subprocess.call(["/usr/bin/fbset", "-depth", "16"])

    def display_image(path, fixed=False):
        opts = ["/usr/bin/fbi", "-T", "1", "-a", "-noverbose"]

        if not fixed:
            opts = opts + ["-oneshot",]

        subprocess.call(opts + [path,])

else:
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
        instance = vlc.Instance('--sub-filter "logo{file=logo.png,opacity=40,x=10,y=10}"')

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
    def __init__(self, http_base_url):
        self.stream_player = None
        self.stream_player_pipe = None
        self.stream_url = None
        self.last_ping = time.time()
        self.http_base_url = http_base_url

        display_image("%s/background.png" % (self.http_base_url))

    @property
    def name(self):
        return self.name

    @name.setter
    def name(self, value):
        self.name = value

    def ping(self):
        self.last_ping = time.time()
        return "pong"

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

        print("Starting stream for %s ..." % (stream_url))
        self.stream_player = multiprocessing.Process(target=stream_player_process, args=(process_pipe, stream_url))
        self.stream_player.start()

    def display_image(self, image_url, stop_stream=True):
        if stop_stream:
            self.stop_stream()

        display_image(image_url)

    def stop_stream(self):
        if self.stream_player_pipe:
            self.stream_player_pipe.send("stop")
            self.stream_player_pipe.close()
            self.stream_player_pipe = None

        display_image("%s/background.png" % (self.http_base_url))

    def get_screenshot(self):
        if running_on_pi():
            ret = subprocess.call(["/usr/bin/raspi2png", "--pngname", "/tmp/screen.png"])

            if ret != 0 or not os.path.exists("/tmp/screen.png"):
                print("Error fetching screenshot!")
                return {"error": True}

            img = Image.open("/tmp/screen.png")

        else:
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

    def reboot(self):
        self.stop_stream()
        subprocess.call(["/usr/bin/reboot"])



def generate_free_name(ns):
    registered_slaves = ns.list(prefix="slave")

    max_num = 0
    for slave, _ in registered_slaves.items():
        if not "." in slave:
            continue

        num = int(slave.split(".")[1])

        if num > max_num:
            max_num = num

    max_num += 1

    return "slave.%d" % (max_num)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: %s <ip addr>" % (sys.argv[0]))
        sys.exit(-1)

    ip = sys.argv[1]

    daemon = Pyro4.Daemon(ip)
    print("Locating nameserver (local ip: %s) ..." % (ip))

    while True:
        try:
            ns = Pyro4.locateNS()
            if ns:
                break
        except Pyro4.errors.NamingError:
            print("Could not locate Nameserver, retrying in 2 seconds ...")
            time.sleep(2)

    # Get IP address of nameserver
    ns_location = ns._pyroUri.location
    http_ip = ns_location[:ns_location.find(":")]
    http_base_url = "http://%s/bcgstreaming/" % (http_ip,)

    sc = StreamSlaveControl(http_base_url)
    uri = daemon.register(sc)

    name = generate_free_name(ns) #"slave-%s" % (hashlib.sha1(ip).hexdigest()[:8])

    print("Registering with nameserver (name: %s) ..." % (name))
    ns.register(name, uri)

    print("Done! Starting event loop ...")
    def pingTimeout(sc):
        return time.time() - sc.last_ping <= 10

    while True:
        try:
            daemon.requestLoop(loopCondition=partial(pingTimeout, sc))
            ns.remove(name=name)
            time.sleep(2)
            sc.last_ping = time.time()
            ns.register(name, uri)
        except KeyboardInterrupt:
            break

    daemon.close()

    print("Removing ourself from the name server ...")
    ns.remove(name)
    print("Good bye!")
