import json
from pathlib import Path
import asyncio
import os
import sys
import platform
import shutil
import glob
import cli_ui
import requests

from src.args import Args
from src.clients import Clients
from src.prep import Prep
from src.trackers.COMMON import COMMON
from src.trackers.HUNO import HUNO
from src.trackers.BLU import BLU
from src.trackers.BHD import BHD
from src.trackers.AITHER import AITHER
from src.trackers.STC import STC
from src.trackers.R4E import R4E
from src.trackers.THR import THR
from src.trackers.STT import STT
from src.trackers.HP import HP
from src.trackers.PTP import PTP
from src.trackers.SN import SN
from src.trackers.ACM import ACM
from src.trackers.HDB import HDB
from src.trackers.LCD import LCD
from src.trackers.TTG import TTG
from src.trackers.LST import LST
from src.trackers.FL import FL
from src.trackers.LT import LT
from src.trackers.NBL import NBL
from src.trackers.ANT import ANT
from src.trackers.PTER import PTER
from src.trackers.MTV import MTV
from src.trackers.JPTV import JPTV
from src.trackers.TL import TL
from src.trackers.TDC import TDC
from src.trackers.HDT import HDT
from src.trackers.RF import RF
from src.trackers.OE import OE
from src.trackers.BHDTV import BHDTV
from src.trackers.RTF import RTF
from src.trackers.ULCX import ULCX
from src.trackers.LDU import LDU


from src.console import console
from rich.markdown import Markdown
from rich.style import Style
from datetime import datetime

cli_ui.setup(color='always', title="Roid Assistant")
import traceback

base_dir = os.path.abspath(os.path.dirname(__file__))

try:
    from data.config import config
except:
    if not os.path.exists(os.path.abspath(f"{base_dir}/data/config.py")):
        try:
            if os.path.exists(os.path.abspath(f"{base_dir}/data/config.json")):
                with open(f"{base_dir}/data/config.json", 'r', encoding='utf-8-sig') as f:
                    json_config = json.load(f)
                    f.close()
                with open(f"{base_dir}/data/config.py", 'w') as f:
                    f.write(f"config = {json.dumps(json_config, indent=4)}")
                    f.close()
                cli_ui.info(cli_ui.green, "Successfully updated config from .json to .py")    
                cli_ui.info(cli_ui.green, "It is now safe for you to delete", cli_ui.yellow, "data/config.json", "if you wish")    
                from data.config import config
            else:
                raise NotImplementedError
        except:
            cli_ui.info(cli_ui.red, "We have switched from .json to .py for config to have a much more lenient experience")
            cli_ui.info(cli_ui.red, "Looks like the auto updater didnt work though")
            cli_ui.info(cli_ui.red, "Updating is just 2 easy steps:")
            cli_ui.info(cli_ui.red, "1: Rename", cli_ui.yellow, os.path.abspath(f"{base_dir}/data/config.json"), cli_ui.red, "to", cli_ui.green, os.path.abspath(f"{base_dir}/data/config.py") )
            cli_ui.info(cli_ui.red, "2: Add", cli_ui.green, "config = ", cli_ui.red, "to the beginning of", cli_ui.green, os.path.abspath(f"{base_dir}/data/config.py"))
            exit()
    else:
        console.print(traceback.print_exc())
client = Clients(config=config)
parser = Args(config)

async def do_the_thing(base_dir):
    meta = {'base_dir': base_dir}
    paths = [os.path.abspath(each) for each in sys.argv[1:] if os.path.exists(each)]

    meta, help, before_args = parser.parse(tuple(' '.join(sys.argv[1:]).split(' ')), meta)

    if meta['cleanup'] and os.path.exists(f"{base_dir}/tmp"):
        shutil.rmtree(f"{base_dir}/tmp")
        console.print("[bold green]Successfully emptied tmp directory")

    if not meta['path']:
        exit(0)

    path = os.path.abspath(meta['path'][:-1] if meta['path'].endswith('"') else meta['path'])

    queue = []
    if os.path.exists(path):
        meta, help, before_args = parser.parse(tuple(' '.join(sys.argv[1:]).split(' ')), meta)
        queue = [path]
    else:
        if os.path.exists(os.path.dirname(path)) and len(paths) <= 1:
            globs = glob.glob(path.replace('[', '[[]'))
            queue = globs
            if queue:
                md_text = "\n - ".join(queue)
                console.print("\n[bold green]Queuing these files:[/bold green]")
                console.print(Markdown(f"- {md_text.rstrip()}\n\n", style=Style(color='cyan')))
            else:
                console.print(f"[red]Path: [bold red]{path}[/bold red] does not exist")
        elif os.path.exists(os.path.dirname(path)) and len(paths) != 1:
            queue = paths
            md_text = "\n - ".join(queue)
            console.print("\n[bold green]Queuing these files:[/bold green]")
            console.print(Markdown(f"- {md_text.rstrip()}\n\n", style=Style(color='cyan')))
        elif not os.path.exists(os.path.dirname(path)):
            split_path = path.split()
            p1 = split_path[0]
            for i, each in enumerate(split_path):
                try:
                    if os.path.exists(p1) and not os.path.exists(f"{p1} {split_path[i+1]}"):
                        queue.append(p1)
                        p1 = split_path[i+1]
                    else:
                        p1 += f" {split_path[i+1]}"
                except IndexError:
                    if os.path.exists(p1):
                        queue.append(p1)
                    else:
                        console.print(f"[red]Path: [bold red]{p1}[/bold red] does not exist")

            if queue:
                md_text = "\n - ".join(queue)
                console.print("\n[bold green]Queuing these files:[/bold green]")
                console.print(Markdown(f"- {md_text.rstrip()}\n\n", style=Style(color='cyan')))
            else:
                # Add Search Here (Implementation not provided)
                console.print(f"[red]There was an issue with your input. If you think this was not an issue, please make a report that includes the full command used.")
                exit()

    base_meta = {k: v for k, v in meta.items()}
    for path in queue:
        meta = base_meta.copy()  # Efficiently copy the base metadata
        meta['path'] = path
        meta['uuid'] = None

        meta_file_path = f"{base_dir}/tmp/{os.path.basename(path)}/meta.json"
        if os.path.exists(meta_file_path):
            with open(meta_file_path) as f:
                saved_meta = json.load(f)

            overwrite_list = {
                'trackers', 'dupe', 'debug', 'anon', 'category', 'type', 'screens', 'nohash', 'manual_edition', 'imdb', 
                'tmdb_manual', 'mal', 'manual', 'hdb', 'ptp', 'blu', 'no_season', 'no_aka', 'no_year', 'no_dub', 'no_tag', 
                'no_seed', 'client', 'desclink', 'descfile', 'desc', 'draft', 'region', 'freeleech', 'personalrelease', 
                'unattended', 'season', 'episode', 'torrent_creation', 'qbit_tag', 'qbit_cat', 'skip_imghost_upload', 
                'imghost', 'manual_source', 'webdv', 'hardcoded-subs'
            }
            meta.update({k: v for k, v in saved_meta.items() if k in overwrite_list and meta.get(k) != v})

        console.print(f"{get_date('info')}[green]Gathering info for {os.path.basename(path)}")
        meta['imghost'] = meta.get('imghost') or config['DEFAULT']['img_host_1']

        if not meta['unattended']:
            meta['unattended'] = config['DEFAULT'].get('auto_mode', False)
            if meta['unattended']:
                console.print(f"{get_date('warn')}[yellow]Running in Auto Mode")

        prep = Prep(screens=meta['screens'], img_host=meta['imghost'], config=config)
        meta = await prep.gather_prep(meta=meta, mode='cli')
        meta['name_notag'], meta['name'], meta['clean_name'], meta['potential_missing'] = await prep.get_name(meta)

        if not meta.get('image_list') and not meta.get('skip_imghost_upload'):
            return_dict = {}
            meta['image_list'], _ = prep.upload_screens(meta, meta['screens'], 1, 0, meta['screens'], [], return_dict)
            if meta['debug']:
                console.print(meta['image_list'])
        elif meta.get('skip_imghost_upload') and not meta.get('image_list'):
            meta['image_list'] = []

        base_torrent_path = os.path.abspath(f"{meta['base_dir']}/tmp/{meta['uuid']}/BASE.torrent")
        if not os.path.exists(base_torrent_path):
            reuse_torrent = None if meta.get('rehash') else await client.find_existing_torrent(meta)
            if reuse_torrent:
                prep.create_base_from_existing_torrent(reuse_torrent, meta['base_dir'], meta['uuid'])
            elif not meta['nohash']:
                prep.create_torrent(meta, Path(meta['path']), "BASE", meta.get('piece_size_max', 0))
            if meta['nohash']:
                meta['client'] = "none"
        elif meta.get('rehash') and not meta['nohash']:
            prep.create_torrent(meta, Path(meta['path']), "BASE", meta.get('piece_size_max', 0))

        if int(meta.get('randomized', 0)) >= 1:
            prep.create_random_torrents(meta['base_dir'], meta['uuid'], meta['randomized'], meta['path'])
    
        if meta.get('trackers', None) != None:
            trackers = meta['trackers']
        else:
            trackers = config['TRACKERS']['default_trackers']
        if "," in trackers:
            trackers = trackers.split(',')
        with open (f"{meta['base_dir']}/tmp/{meta['uuid']}/meta.json", 'w') as f:
            json.dump(meta, f, indent=4)
            f.close()

        confirm = get_confirmation(meta)
        while not confirm:
            editargs = cli_ui.ask_string("Input args that need correction e.g.(--tag NTb --category tv --tmdb 12345)")
            editargs = (meta['path'],) + tuple(editargs.split())
            if meta['debug']:
                editargs += ("--debug",)

            meta, help, before_args = parser.parse(editargs, meta)
            meta['edit'] = True
            meta = await prep.gather_prep(meta=meta, mode='cli')
            meta['name_notag'], meta['name'], meta['clean_name'], meta['potential_missing'] = await prep.get_name(meta)
            confirm = get_confirmation(meta)

        trackers = [trackers] if isinstance(trackers, str) else trackers  # Ensure trackers is always a list
        trackers = [s.strip().upper() for s in trackers]
        if meta.get('manual', False):
            trackers.insert(0, "MANUAL")

        """
        Upload to trackers.
        """
        common = COMMON(config=config)
        api_trackers = ['BLU', 'AITHER', 'STC', 'R4E', 'STT', 'RF', 'ACM','LCD','LST','HUNO', 'SN', 'LT', 'NBL', 'ANT', 'JPTV', 'TDC', 'OE', 'BHDTV', 'RTF', 'ULCX', 'LDU']
        http_trackers = ['HDB', 'TTG', 'FL', 'PTER', 'HDT', 'MTV']
        tracker_class_map = {
            'BLU' : BLU, 'BHD': BHD, 'AITHER' : AITHER, 'STC' : STC, 'R4E' : R4E, 'THR' : THR, 'STT' : STT, 'HP' : HP, 'PTP' : PTP, 'RF' : RF, 'SN' : SN, 
            'ACM' : ACM, 'HDB' : HDB, 'LCD': LCD, 'TTG' : TTG, 'LST' : LST, 'HUNO': HUNO, 'FL' : FL, 'LT' : LT, 'NBL' : NBL, 'ANT' : ANT, 'PTER': PTER, 'JPTV' : JPTV,
            'TL' : TL, 'TDC' : TDC, 'HDT' : HDT, 'MTV': MTV, 'OE': OE, 'BHDTV': BHDTV, 'RTF':RTF, 'ULCX' : ULCX, 'LDU' : LDU}

        for tracker in trackers:
            if meta['name'].endswith('DUPE?'):
                meta['name'] = meta['name'].replace(' DUPE?', '')
            tracker = tracker.replace(" ", "").upper().strip()
            if meta['debug']:
                debug = "(DEBUG)"
            else:
                debug = ""
            
            if tracker in api_trackers:
                tracker_class = tracker_class_map[tracker](config=config)
                if meta['unattended']:
                    upload_to_tracker = True
                else:
                    upload_to_tracker = cli_ui.ask_yes_no(f"Upload to {tracker_class.tracker}? {debug}", default=meta['unattended'])
                if upload_to_tracker:
                    console.print(f"{get_date('info')}[bold green]Uploading to {tracker_class.tracker}")
                    if check_banned_group(tracker_class.tracker, tracker_class.banned_groups, meta):
                        continue
                    dupes = await tracker_class.search_existing(meta)
                    dupes = await common.filter_dupes(dupes, meta)
                    # note BHDTV does not have search implemented.
                    meta = dupe_check(dupes, meta)
                    if meta['upload'] == True:
                        await tracker_class.upload(meta)
                        if tracker == 'SN':
                            await asyncio.sleep(16)
                        await client.add_to_client(meta, tracker_class.tracker)
            
            if tracker in http_trackers:
                tracker_class = tracker_class_map[tracker](config=config)
                if meta['unattended']:
                    upload_to_tracker = True
                else:
                    upload_to_tracker = cli_ui.ask_yes_no(f"Upload to {tracker_class.tracker}? {debug}", default=meta['unattended'])
                if upload_to_tracker:
                    console.print(f"Uploading to {tracker}")
                    if check_banned_group(tracker_class.tracker, tracker_class.banned_groups, meta):
                        continue
                    if await tracker_class.validate_credentials(meta) == True:
                        dupes = await tracker_class.search_existing(meta)
                        dupes = await common.filter_dupes(dupes, meta)
                        meta = dupe_check(dupes, meta)
                        if meta['upload'] == True:
                            await tracker_class.upload(meta)
                            await client.add_to_client(meta, tracker_class.tracker)

            if tracker == "MANUAL":
                if meta['unattended']:                
                    do_manual = True
                else:
                    do_manual = cli_ui.ask_yes_no(f"Get files for manual upload?", default=True)
                if do_manual:
                    for manual_tracker in trackers:
                        if manual_tracker != 'MANUAL':
                            manual_tracker = manual_tracker.replace(" ", "").upper().strip()
                            tracker_class = tracker_class_map[manual_tracker](config=config)
                            if manual_tracker in api_trackers:
                                await common.unit3d_edit_desc(meta, tracker_class.tracker, tracker_class.signature)
                            else:
                                await tracker_class.edit_desc(meta)
                    url = await prep.package(meta)
                    if url == False:
                        console.print(f"{get_date('warn')}[yellow]Unable to upload prep files, they can be found at `tmp/{meta['uuid']}")
                    else:
                        console.print(f"{get_date('info')}[green]{meta['name']}")
                        console.print(f"{get_date('info')}[green]Files can be found at: [yellow]{url}[/yellow]")  

            if tracker == "BHD":
                bhd = BHD(config=config)
                draft_int = await bhd.get_live(meta)
                if draft_int == 0:
                    draft = "Draft"
                else:
                    draft = "Live"
                if meta['unattended']:
                    upload_to_bhd = True
                else:
                    upload_to_bhd = cli_ui.ask_yes_no(f"Upload to BHD? ({draft}) {debug}", default=meta['unattended'])
                if upload_to_bhd:
                    console.print("Uploading to BHD")
                    if check_banned_group("BHD", bhd.banned_groups, meta):
                        continue
                    dupes = await bhd.search_existing(meta)
                    dupes = await common.filter_dupes(dupes, meta)
                    meta = dupe_check(dupes, meta)
                    if meta['upload'] == True:
                        await bhd.upload(meta)
                        await client.add_to_client(meta, "BHD")
            
            if tracker == "THR":
                if meta['unattended']:
                    upload_to_thr = True
                else:
                    upload_to_thr = cli_ui.ask_yes_no(f"Upload to THR? {debug}", default=meta['unattended'])
                if upload_to_thr:
                    console.print("Uploading to THR")
                    #Unable to get IMDB id/Youtube Link
                    if meta.get('imdb_id', '0') == '0':
                        imdb_id = cli_ui.ask_string("Unable to find IMDB id, please enter e.g.(tt1234567)")
                        meta['imdb_id'] = imdb_id.replace('tt', '').zfill(7)
                    if meta.get('youtube', None) == None:
                        youtube = cli_ui.ask_string("Unable to find youtube trailer, please link one e.g.(https://www.youtube.com/watch?v=dQw4w9WgXcQ)")
                        meta['youtube'] = youtube
                    thr = THR(config=config)
                    try:
                        with requests.Session() as session:
                            console.print(f"{get_date('warn')}[yellow]Logging in to THR")
                            session = thr.login(session)
                            console.print(f"{get_date('warn')}[yellow]Searching for Dupes")
                            dupes = thr.search_existing(session, meta.get('imdb_id'))
                            dupes = await common.filter_dupes(dupes, meta)
                            meta = dupe_check(dupes, meta)
                            if meta['upload'] == True:
                                await thr.upload(session, meta)
                                await client.add_to_client(meta, "THR")
                    except:
                        console.print(traceback.print_exc())

            if tracker == "PTP":
                if meta['unattended']:
                    upload_to_ptp = True
                else:
                    upload_to_ptp = cli_ui.ask_yes_no(f"Upload to {tracker}? {debug}", default=meta['unattended'])
                if upload_to_ptp:
                    console.print(f"Uploading to {tracker}")
                    if meta.get('imdb_id', '0') == '0':
                        imdb_id = cli_ui.ask_string("Unable to find IMDB id, please enter e.g.(tt1234567)")
                        meta['imdb_id'] = imdb_id.replace('tt', '').zfill(7)
                    ptp = PTP(config=config)
                    if check_banned_group("PTP", ptp.banned_groups, meta):
                        continue
                    try:
                        console.print(f"{get_date('warn')}[yellow]Searching for Group ID")
                        groupID = await ptp.get_group_by_imdb(meta['imdb_id'])
                        if groupID == None:
                            console.print(f"{get_date('warn')}[yellow]No Existing Group found")
                            if meta.get('youtube', None) == None or "youtube" not in str(meta.get('youtube', '')):
                                youtube = cli_ui.ask_string("Unable to find youtube trailer, please link one e.g.(https://www.youtube.com/watch?v=dQw4w9WgXcQ)", default="")
                                meta['youtube'] = youtube
                            meta['upload'] = True
                        else:
                            console.print(f"{get_date('warn')}[yellow]Searching for Existing Releases")
                            dupes = await ptp.search_existing(groupID, meta)
                            dupes = await common.filter_dupes(dupes, meta)
                            meta = dupe_check(dupes, meta)
                        if meta.get('imdb_info', {}) == {}:
                            meta['imdb_info'] = await prep.get_imdb_info(meta['imdb_id'], meta)
                        if meta['upload'] == True:
                            ptpUrl, ptpData = await ptp.fill_upload_form(groupID, meta)
                            await ptp.upload(meta, ptpUrl, ptpData)
                            await asyncio.sleep(5)
                            await client.add_to_client(meta, "PTP")
                    except:
                        console.print(traceback.print_exc())

            if tracker == "TL":
                tracker_class = tracker_class_map[tracker](config=config)
                if meta['unattended']:
                    upload_to_tracker = True
                else:
                    upload_to_tracker = cli_ui.ask_yes_no(f"Upload to {tracker_class.tracker}? {debug}", default=meta['unattended'])
                if upload_to_tracker:
                    console.print(f"Uploading to {tracker_class.tracker}")
                    if check_banned_group(tracker_class.tracker, tracker_class.banned_groups, meta):
                        continue
                    await tracker_class.upload(meta)
                    await client.add_to_client(meta, tracker_class.tracker)            

def get_date(level):
    """
    YYYY-MM-DD HH:MM:SS  INFO   DETAIL
    YYYY-MM-DD HH:MM:SS  WARN   DETAIL
    YYYY-MM-DD HH:MM:SS  ALERT  DETAIL
    """
    if level == "info":
        return f"[blue]{datetime.today().strftime('%Y-%m-%d-%H:%M:%S') + '[green]'+'INFO'.center(9, ' ')}"
    elif level == "info_white":
        return f"{datetime.today().strftime('%Y-%m-%d-%H:%M:%S') + 'INFO'.center(9, ' ')}"
    elif level == "warn":
        return f"[blue]{datetime.today().strftime('%Y-%m-%d-%H:%M:%S') + '[yellow]'+'WARN'.center(9, ' ')}"
    else:
        return f"[blue]{datetime.today().strftime('%Y-%m-%d-%H:%M:%S') + '[red]'+'ALERT'.center(9, ' ')}"

def get_confirmation(meta):
    """
    Prints all the torrent information & metadata to get user confirmation before uploading,
    will skip the confirmation if unattended is passed.
    """
    if meta['debug']:
        console.print(f"{get_date('alert')}[bold red]DEBUG: True")

    console.print(f"{get_date('info')}[bold green]Prep material saved to {meta['base_dir']}/tmp/{meta['uuid']}")

    console.print(f"{get_date('info_white')}Database Info")
    console.print(f"{get_date('info_white')}Title: {meta['title']} ({meta['year']})")
    console.print(f"{get_date('info_white')}Overview: {meta['overview']}")
    console.print(f"{get_date('info_white')}Category: {meta['category']}")

    if int(meta.get('tmdb', 0)):
        console.print(f"{get_date('info_white')}TMDB: https://www.themoviedb.org/{meta['category'].lower()}/{meta['tmdb']}")
    if int(meta.get('imdb_id', '0')):
        console.print(f"{get_date('info_white')}IMDB: https://www.imdb.com/title/tt{meta['imdb_id']}")
    if int(meta.get('tvdb_id', '0')):
        console.print(f"{get_date('info_white')}TVDB: https://www.thetvdb.com/?id={meta['tvdb_id']}&tab=series")
    if int(meta.get('mal_id', 0)):
        console.print(f"{get_date('info_white')}MAL : https://myanimelist.net/anime/{meta['mal_id']}")

    if int(meta.get('freeleech', '0')):
        console.print(f"{get_date('info_white')}Freeleech: {meta['freeleech']}")
    
    tag = f" / {meta['tag'][1:]}" if meta['tag'] else "" 
    res = meta['source'] if meta['is_disc'] == "DVD" else meta['resolution']
    console.print(f"{get_date('info_white')}{res} / {meta['type']}{tag}")

    if meta.get('personalrelease', False):
        console.print(f"{get_date('info_white')}Personal Release!")

    if not meta.get('unattended', False):
        get_missing(meta)
        ring_the_bell = "\a" if config['DEFAULT'].get("sfx_on_prompt", True) else ""  
        console.print(f"Is this correct?{ring_the_bell}")
        console.print(f"{get_date('info_white')}Name: {meta['name']}")
        confirm = cli_ui.ask_yes_no(f"{get_date('info_white')}Correct?", default=False)
    else: 
        console.print(f"{get_date('info_white')}Name: {meta['name']}")
        confirm = True

    return confirm

def dupe_check(dupes, meta):
    """
    Searches the site for the torrent to check if there are any similar releases,
    will set meta['upload'] to True if there are no dupes or if skip-dupe-check is passed.
    """
    if not dupes:
        console.print(f"{get_date('info')}[green]No dupes found")
        meta['upload'] = True
        return meta

    dupe_text = "\n".join(dupes)
    console.print(f"{get_date('info')}[bold green]Are these dupes?")
    console.print(f"{get_date('info_white')}{dupe_text}")

    skip_dupe_check = meta.get('dupe', False)
    if meta['unattended']:
        upload = skip_dupe_check
        message = f"{get_date('warn')}[yellow]Found potential dupes. --skip-dupe-check was passed. Uploading anyways" if upload else "[red]Found potential dupes. Aborting. If this is not a dupe, or you would like to upload anyways, pass --skip-dupe-check"
        console.print(message)
    else:
        upload = cli_ui.ask_yes_no(f"{get_date('info')}[bold green]Upload Anyways?", default=False) if not skip_dupe_check else True

    meta['upload'] = upload
    if upload and meta['name'] in dupes:
        meta['name'] = f"{get_date('info')}[bold green]{meta['name']} DUPE?"
    return meta

def check_banned_group(tracker, banned_group_list, meta):
    """
    Verifies if the release group is on the trackers list of banned groups, 
    Returns false if it's banned.
    """
    if not meta['tag']:
        return False

    for tag in banned_group_list:
        match = meta['tag'][1:].lower() == tag[0].lower() if isinstance(tag, list) else meta['tag'][1:].lower() == tag.lower()
        if match:
            console.print(f"[bold yellow]{meta['tag'][1:]}[/bold yellow][bold red] was found on [bold yellow]{tracker}'s[/bold yellow] list of banned groups.")
            if isinstance(tag, list):
                console.print(f"{get_date('alert')}[bold red]NOTE: [bold yellow]{tag[1]}")

            if not cli_ui.ask_yes_no(cli_ui.red, f"{get_date('info')}[bold red]Upload Anyways?", default=False):
                return True
    return False

def get_missing(meta):
    """
    Determines if there may be any missing information like "directors cut",
    will print any information that wasn't specified.
    """
    info_notes = {
        'edition' : 'Special Edition/Release',
        'description' : "Please include Remux/Encode Notes if possible (either here or edit your upload)",
        'service' : "WEB Service e.g.(AMZN, NF)",
        'region' : "Disc Region",
        'imdb' : 'IMDb ID (tt1234567)',
        'distributor' : "Disc Distributor e.g.(BFI, Criterion, etc)"
    }

    if meta.get('imdb_id', '0') == '0':
        meta['imdb_id'] = '0'
        meta['potential_missing'].append('imdb_id')

    missing = [f"--{each if each != 'imdb_id' else 'imdb'} | {info_notes.get(each, '')}" for each in meta['potential_missing'] if str(meta.get(each, '')).replace(' ', '') in ["", "None", "0"]]

    if missing:
        cli_ui.info_section(cli_ui.yellow, "Potentially missing information:")
        for each in missing:
            cli_ui.info(cli_ui.red if each.split('|')[0].replace('--', '').strip() in ["imdb"] else cli_ui.white, each)

if __name__ == '__main__':
    try:
        pyver = platform.python_version_tuple()
        if int(pyver[0]) != 3:
            console.print(f"{get_date('alert')}[bold red]Python2 Detected, please use python3")
            exit()
        elif int(pyver[1]) <= 6:
            console.print(f"{get_date('alert')}[bold red]Python <= 3.6 Detected, please use Python >=3.7")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(do_the_thing(base_dir))
        else:
            asyncio.run(do_the_thing(base_dir))
    except KeyboardInterrupt:
        console.print(f"{get_date('alert')}[bold red]Exiting: Keyboard Interrupt")
    except Exception as err:
        console.print(f"{get_date('alert')}[bold red]Exiting: {err}")
