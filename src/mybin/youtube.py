#!/usr/bin/python3

import argparse
import subprocess
import yt_dlp

#need to replace youtube-dl by yt-dlp
## look at https://www.tglyn.ch/blog/youtube_download_for_djs/
## to creatre a playlist folder into which ALL files are placed.

description = """
Downloader of youtube file (audio or video) and playlist.
The tool creates a directory that is the title of the playlist of video. 
All information / audio and video files ar eplace under that directory.

To download a video or a video playlist 
ytd url

To download the audio file or an audio playlist
ytd --audio url


It is based on yt-dlp https://github.com/yt-dlp/yt-dlp#output-template

"""


def play_list_title( url ):
  """return the title of a play list

  We use that fucntion to create a specific directory
  associated to the playlist, that directory will contain other 
  for each song a specific directory
  """

  ydl_opts = {}
  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info( url, download=False)
  play_list_title = f"{info[ 'title' ]}--{info[ 'id' ]}"
  for c in [ '/', '\\' ]: 
    play_list_title = play_list_title.replace( c, '-' ) 
  for c in [ '*', '?', '"', "'", '<', '>', '|' ]: 
    play_list_title = play_list_title.replace( c, '' ) 
  return play_list_title




def ytd_cli():

  description = """
  Downloading videos and audio from Youtube
  """
  parser = argparse.ArgumentParser( description=description )
  parser.add_argument( 'url',  type=ascii, nargs=1, help="The Youtube URL" )
  parser.add_argument( '-start', '--playlist_start', type=int, nargs='?', \
    default=1, help="Starting Playlist Track" )
  parser.add_argument( '-end', '--playlist_end', type=int, nargs='?', \
    default=0, help="Stop Playlist Track" )
  parser.add_argument( '-audio', '--audio', default=False,  \
    action='store_const', const=True, \
    help="""Download Audio (only) Format. Only needed if one if willing
             to be able to listen to the media in an audio only mode.""" )
  args = parser.parse_args()
  print( args )

  ytd( args.url[ 0 ][ 1: -1 ], 
       playlist_start=args.playlist_start, \
       playlist_end=args.playlist_end, \
       audio=args.audio)


def ytd( url, playlist_start:int=0, playlist_end:int=0, audio:bool=False ):

  directory = play_list_title( url )

  ydl_opts = {'extract_flat': 'discard_in_playlist',
         'fragment_retries': 10,
         'ignoreerrors': True,
         'outtmpl': {'default': f"{directory}/%(title)s--%(id)s.%(ext)s"},
         'postprocessors': [{'add_chapters': True,
                             'add_infojson': 'if_exists',
                             'add_metadata': True,
                             'key': 'FFmpegMetadata'},
                            {'already_have_thumbnail': True, 'key': 'EmbedThumbnail'},
                            {'key': 'FFmpegConcat',
                             'only_multi_video': True,
                             'when': 'playlist'}],
         'retries': 10,
         'writeannotations': True,
         'writedescription': True,
         'writeinfojson': True,
         'writethumbnail': True}


  if audio is True:
    ydl_opts[ 'format' ]= 'bestaudio/best'
    ydl_opts[ 'postprocessors' ].insert( 0, {'key': 'FFmpegExtractAudio',
                                        'nopostoverwrites': False,
                                        'preferredcodec': 'best',
                                        'preferredquality': '5'} )
  ## Determine if this is a list
  if 'list' in url:
    ydl_opts[ 'playliststart' ] = playlist_start
    if playlist_end != 0:
      ydl_opts[ 'playlistend' ] = playlist_end
    ydl_opts[ 'outtmpl' ] = { 'default' : f"{directory}/%(playlist_index)s--%(title)s--%(id)s" }

  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    error_code = ydl.download( url )


if __name__ == '__main__' :
  ## playlist  
#  url = "https://www.youtube.com/playlist?list=OLAK5uy_n8SMZMZaZTV3tIn7P6a3XRlQB1w4ZEpuM"  
#  ytd( url, audio=True, playlist_end=2)
  ## single audio
  url = "https://www.youtube.com/watch?v=SVHNKv6KQlI"
  ytd( url, audio=True )
  ytd( url )

