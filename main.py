import ffmpy
import time
import datetime
import os
import os.path
import numpy as np
from PIL import Image
import sys
from rich.console import Console
from rich.table import Table
from rich.progress import track

def realtime():
    return datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

def write_log_line(line):
    print(line)
    FILE = 'log.txt'
    with open(FILE, 'a') as f:
        f.write(line + "\n")


def make_frames(file, output):
    ff = ffmpy.FFmpeg(
        executable='C:\\ffmpeg\\bin\\ffmpeg.exe',
        inputs={file: "-skip_frame nokey -loglevel quiet -stats"},
        outputs={output: '-r 1 -vf scale=960:-1 -sws_flags bilinear'})
        # outputs={output: '-r 1'})
    # print(f"Command:\n {ff.cmd}")
    ff.run()
    return


def return_check_zones(file, channel):
    img = np.array(Image.open(file))
    c_sx = np.mean(img[250:270, 20:60, channel])
    c_dx = np.mean(img[250:270, 900:940, channel])
    c_cc = np.mean(img[275:280, 460:500, channel])
    return (c_sx, c_cc, c_dx)

def count_white_pixels(file, threshold=230):
    img = np.array(Image.open(file).convert('L'))
    whites = img[247:272, 85:875] > threshold
    # Image.fromarray(whites).show()
    return (whites.sum())

def check_if_bar(file, channel=0, language="it"):

    W_THRESHOLD = 230
    MIN_DIFFERENCE = 30

    MIN_RED = 140
    MAX_BLUE = 60
    MAX_GREEN = 105

    check_zones_r =  return_check_zones(file, 0)
    check_zones_b =  return_check_zones(file, 2)
    check_zones_g =  return_check_zones(file, 1)

    pixel_count = count_white_pixels(file, W_THRESHOLD)

    r_w_MIN, r_w_MAX = (200, 900)
    b_w_MIN, b_w_MAX = (90, 500)


    if ((all(i > MIN_RED for i in check_zones_r))  # i quadrati dx e sx sono rossi
        and (all(i < MAX_BLUE for i in check_zones_b))  # i quadrati dx e sx NON sono blu
        and (all(i < MAX_GREEN for i in check_zones_g))  # i quadrati dx e sx NON sono verdi
        and (r_w_MIN < pixel_count < r_w_MAX)  # ci sono i pixel bianchi al centro
        ):
        return (True, "rossa")

    MIN_BLUE = 140

    MAX_RED = 60
    return (True, "blu") if ((all(i > MIN_BLUE for i in check_zones_b)) and (all(i < MAX_RED for i in check_zones_r)) and (all(i < MAX_GREEN for i in check_zones_g)) and (b_w_MIN < pixel_count < b_w_MAX)) else (False, None)  # i quadrati dx e sx sono blu  # i quadrati dx e sx NON sono rossi  # i quadrati dx e sx NON sono verdi  # ci sono i pixel bianchi al centro

TEST = False

framesdirectory = 'frames'
output = "frames/output_%04d.jpg"


for file in sys.argv[1:]:
    start = time.time()

    if TEST:
        framesdirectory = 'test'

    l = int(len(file) + 4)

    write_log_line(f"{'#'*l}\n# {file} #\n{'#'*l}\n")

    write_log_line(f"{realtime()} Estraggo i frame")

    if not TEST:
        make_frames(file, output)

    write_log_line(f'{realtime()} Estrazione completata in {time.time()-start:.2f} secondi.')
    write_log_line(f"{realtime()} Inizio l'analisi dei frame...")

    table = Table(title="Risultati")
    table.add_column("Timecode")
    table.add_column("Nome File")
    table.add_column("Colore Barra")

    c = 0

    total_files = len([f for f in os.listdir(framesdirectory) if os.path.isfile(os.path.join(framesdirectory, f))])

    for filename in track(os.scandir(framesdirectory), description="Analizzando...", total=total_files, transient=True):
        if filename.is_file():
            has_bar, bar_color = check_if_bar(filename.path)
            if has_bar:
                c += 1
                timecode = datetime.timedelta(seconds=int(filename.path[-8:-4]))
                table.add_row(str(timecode), filename.name, "🟥 Rossa" if bar_color == 'rossa' else "🟦 Blu")
                write_log_line(f"{realtime()} · [{str(timecode)}] Trovata striscia {bar_color} ({filename.name})")

            elif not TEST:
                os.remove(filename.path)
    write_log_line(f"{realtime()} Controllati {total_files} frames.\n")

    if c == 0:
        write_log_line(f"{realtime()} Nessun frame con striscia blu o rossa trovato.\n")
    else:
        console = Console()
        console.print(table)

    write_log_line(f"{realtime()} Analisi terminata\n\n")

input("Premi invio per continuare..")
