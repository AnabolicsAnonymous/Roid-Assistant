# -*- coding: utf-8 -*-
# import discord
import asyncio
import requests
import distutils.util
import os
import platform

from src.trackers.COMMON import COMMON
from src.console import console
from datetime import datetime

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

class ULCX():
    """
    Edit for Tracker:
        Edit BASE.torrent with announce and source
        Check for duplicates
        Set type/category IDs
        Upload
    """

    ###############################################################
    ########                    EDIT ME                    ########
    ###############################################################

    # ALSO EDIT CLASS NAME ABOVE

async def upload(self, meta):
    common = COMMON(config=self.config)
    await common.edit_torrent(meta, self.tracker, self.source_flag)

    anon = 0 if meta['anon'] == 0 and not self.config['TRACKERS'][self.tracker].get('anon', False) else 1

    if meta['bdinfo']:
        with open(f"{meta['base_dir']}/tmp/{meta['uuid']}/BD_SUMMARY_00.txt", 'r', encoding='utf-8') as f:
            bd_dump = f.read()
        mi_dump = None
    else:
        with open(f"{meta['base_dir']}/tmp/{meta['uuid']}/MEDIAINFO.txt", 'r', encoding='utf-8') as f:
            mi_dump = f.read()
        bd_dump = None

    with open(f"{meta['base_dir']}/tmp/{meta['uuid']}/[{self.tracker}]DESCRIPTION.txt", 'r') as f:
        desc = f.read()

    with open(f"{meta['base_dir']}/tmp/{meta['uuid']}/[{self.tracker}]{meta['clean_name']}.torrent", 'rb') as open_torrent:
        files = {'torrent': open_torrent}
        data = {
            'name': meta['name'],
            'description': desc,
            'mediainfo': mi_dump,
            'bdinfo': bd_dump,
            'category_id': await self.get_cat_id(meta['category']),
            'type_id': await self.get_type_id(meta['type']),
            'resolution_id': await self.get_res_id(meta['resolution']),
            'tmdb': meta['tmdb'],
            'imdb': meta['imdb_id'].replace('tt', ''),
            'tvdb': meta['tvdb_id'],
            'mal': meta['mal_id'],
            'igdb': 0,
            'anonymous': anon,
            'stream': meta['stream'],
            'sd': meta['sd'],
            'keywords': meta['keywords'],
            'personal_release': int(meta.get('personalrelease', False)),
            'internal': 0,
            'featured': 0,
            'free': 0,
            'doubleup': 0,
            'sticky': 0,
        }
        
        await common.unit3d_edit_desc(meta, self.tracker, self.signature)
        region_id = await common.unit3d_region_ids(meta.get('region'))
        distributor_id = await common.unit3d_distributor_ids(meta.get('distributor'))

        if region_id:
            data['region_id'] = region_id
        if distributor_id:
            data['distributor_id'] = distributor_id

        if meta.get('category') == "TV":
            data['season_number'] = meta.get('season_int', '0')
            data['episode_number'] = meta.get('episode_int', '0')

        # Internal handling (unchanged)
        if self.config['TRACKERS'][self.tracker].get('internal', False) and meta['tag'] != "" and (meta['tag'][1:] in self.config['TRACKERS'][self.tracker].get('internal_groups', [])):
            data['internal'] = 1

        headers = {'User-Agent': f'Roid Assistant/0.0.1 ({platform.system()} {platform.release()})'}
        params = {'api_token': self.config['TRACKERS'][self.tracker]['api_key'].strip()}

        if not meta['debug']:
            response = requests.post(url=self.upload_url, files=files, data=data, headers=headers, params=params)
            try:
                console.print(response.json())
            except:
                console.print(f"{get_date('info')}[bold green]It may have uploaded, go check")
        else:
            console.print(f"[cyan]Request Data:")
            console.print(data)

    async def search_existing(self, meta):
        console.print(f"{get_date('warn')}[yellow]Searching for existing torrents on site...")

        params = {
            'api_token': self.config['TRACKERS'][self.tracker]['api_key'].strip(),
            'tmdbId': meta['tmdb'],
            'categories[]': await self.get_cat_id(meta['category']),
            'types[]': await self.get_type_id(meta['type']),
            'resolutions[]': await self.get_res_id(meta['resolution']),
            'name': meta.get('edition', "") 
        }

        try:
            response = requests.get(url=self.search_url, params=params).json()
            dupes = [each['attributes']['name'] for each in response['data']] 
        except:
            console.print(f'{get_date("alert")}[bold red]Unable to search for existing torrents on site. Either the site is down or your API key is incorrect')
            await asyncio.sleep(5)  

        return dupes
