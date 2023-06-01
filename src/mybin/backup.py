#!/usr/bin/python3

#from cryptography.hazmat.primitives import hashes
import os
import binascii 
import argparse
import subprocess

""" This modules defines some backup procedures

Backup is only performed between a limited number of devices,
and a limited type of medias.  
Backup are repeated task, but when performed manually, we always 
need to make sure that we did not mess up with various directories,
in which case, we may end up in multiple copies of the backup 
which creates a space issue. 

This module aims at building, testing automated commands, that 
when we have enough confidence, we can automated. 
It also enable to trigger manually the commands without entering 
in all configuration details.  

Each backup procedure is defined as a context.
In our case the procedures we defined are: 'desktop-to-nas', 'nas-to-veracrypt' and 'nas-to-hd'.
In each context, a given media is backup. 
In our case we defined the 'home', 'photos', 'videos', 'music'.

Fundamentally, we need context and media, as backup do not really
contains the same data nor are organized the same way. In addition,
backup procedures do take quite a long time, so in many cases, we 
would like to be able to perform some partial backup.  
Typically the Desktop only contains the most recent data, and its 
organization does not match the one from the NAS. 
Backup are also limited by the capacity of the hardware, in that 
sense, the veracrypt backup on only sync the Photos. 
The different path involved are defined below as well as include and exclude file pattern.

In the 'desktop-to-nas' context updates from the DESKTOP is copied to the NAS:
* DESKTOP_MUSIC_DIR -> NAS_MUSIC_DIR 
* DESKTOP_VIDEOS_DIR -> NAS_VIDEOS_DIR
* DESKTOP_PHOTOS_DIR -> NAS_PHOTOS_DIR
* DESKTOP_HOME_DIR -> NAS_HOME_DIR

In the context of 'nas-to-veracrypt' the photo directory is copied to the disk encrypted
*  NAS_PHOTOS_DIR -> VERACRYPT_PHOTOS_DIR

In the context of 'nas-to-hd' the full NAS is synced with the HD:
* NAS_MUSIC_DIR -> HD_MUSIC_DIR
* NAS_VIDEOS_DIR -> HD_VIDEOS_DIR
* NAS_PHOTOS_DIR -> HD_PHOTOS_DIR
* NAS_HOME_DIR -> HD_HOME_DIR
* NAS_HOMES_DIR -> HD_HOMES_DIR (for the full NAS)

TO DO:
* cleam up NAS data - photos, work directory, mail
* rename directories to have default values from Linux Desktop
* enable the reverse check with --delete 
* should configuration be stored in a yaml file ?
    
"""

DESKTOP_MUSIC_DIR = '/home/mglt/myMusic/'
DESKTOP_VIDEOS_DIR = '/home/mglt/myVideos/'
DESKTOP_PHOTOS_DIR = '/home/mglt/myPhotos/'
DESKTOP_HOME_DIR = '/home/mglt/'

NAS_MUSIC_DIR = 'dan@nas.local:/volume1/homes/dan/music/myMusic/'
NAS_VIDEOS_DIR = 'dan@nas.local:/volume1/homes/dan/myVideos/'
NAS_PHOTOS_DIR = 'dan@nas.local:/volume1/homes/dan/myPhotos/'
## when used as a detsination NAS_HOME_DIR can be expressed without ending with '/'
## However to designates all files and subdirectorires as a source -- that is when 
## copied to the HD, we MUST provide the '/'  
NAS_HOME_DIR = 'dan@nas.local:/volume1/homes/dan/work/ericsson/emigdan/'
NAS_HOMES_DIR = 'dan@nas.local:/volume1/homes/'

VERACRYPT_PHOTOS_DIR = '/media/veracrypt1/'

HD_HOMES_DIR = '/media/mglt/78be87ca-9f00-4187-ac55-06fc4ba89844/homes/'
HD_MUSIC_DIR = os.path.join( HD_HOMES_DIR, 'dan', 'music', 'myMusic' )
HD_PHOTOS_DIR = os.path.join( HD_HOMES_DIR, 'dan', 'myPhotos' )
HD_VIDEOS_DIR = os.path.join( HD_HOMES_DIR, 'dan', 'myVideos' )
HD_HOME_DIR = os.path.join( HD_HOMES_DIR, 'dan', 'work', 'ericsson', 'emigdan' )


## These designates important files that are likely exclude otherwise by generic patterns
INCLUDE = [ '.ssh', '.thunderbird',  ]

## designates patterns that are not necessary to backup 
EXCLUDE = [ \
## usually contains .local with a lot of cached files or configuration files
 '/.*',  
## vim temporary files
'*.swp',  '*.swo', '*.swm',
## python tenmprary files
'*$py.class', '*.pyc', '*.pyo', '*.pyd', '.pylintrc', '.ipynb_checkpoints/', '__pycache__/', 
## Apple temporary files
'.DS_Store', 
## latex temprary files
'*.aux', '*.blg', '*.log', '*.out', '*.bbl', 
## Common installation directories
'gems', 'gopath', 'snap', 'perl5',
## Specific directories  
'Downloads',
## backup of the linux laptop (expected to be already on the NAS)
'emc-mglt/', 
'gitlab_*.tgz',
## backup of the windows laptop
'win.bkp', 
]

LOG_FILE = '/tmp/mybackup.log'


def src( ctx, media  ):
  """ returns the appropriated src directory given a context and media

  Args:
    ctx: backups are not generic and only a small number of context exists.
      the context we are considering are 'desktop-to-nas', 'nas-to-veracrypt'
      and 'nas-to-hd'
    media: describes the media being backup. the media considered are 'photos'
      'videos', 'home' and 'music'
  Returns:
    src_dir: the directory that contains the media. This directory is being backup. 
  """

  if ctx == 'desktop-to-nas' :
    if media =='music':
      return DESKTOP_MUSIC_DIR
    elif media == 'videos':
      return DESKTOP_VIDEOS_DIR
    elif media == 'photos':
      return DESKTOP_PHOTOS_DIR
    elif media == 'home':
      return DESKTOP_HOME_DIR  
    else:
      raise ValueError( f"unknown media {media} for {ctx}" )
  elif ctx == 'nas-to-veracrypt' :
    if media == 'photos':
      return NAS_PHOTOS_DIR
    else:
      raise ValueError( f"unknown media {media} for {ctx}" )
  elif ctx == 'nas-to-hd' :
    if media =='music':
      return NAS_MUSIC_DIR
    elif media == 'videos':
      return NAS_VIDEOS_DIR
    elif media == 'photos':
      return NAS_PHOTOS_DIR
    elif media == 'home':
      return NAS_HOME_DIR  
    elif media == 'homes' :
      return NAS_HOMES_DIR
    else:
      raise ValueError( f"unknown media {media} for {ctx}" )
  else:
    raise ValueError( f"unknown ctx {ctx}" )



def dst( ctx, media ):      
  """ returns the appropriated dst directory given a context and media

  Args:
    ctx: backups are not generic and only a small number of context exists.
      the context we are considering are 'desktop-to-nas', 'nas-to-veracrypt'
      and 'nas-to-hd'
    media: describes the media being backup. the media considered are 'photos'
      'videos', 'home' and 'music'
  Returns:
    local_dir: the directory that contains the media. This directory is being backup. 
  """

  if ctx == 'desktop-to-nas' :
    if media =='music':
      return NAS_MUSIC_DIR
    elif media == 'videos':
      return NAS_VIDEOS_DIR
    elif media == 'photos':
      return NAS_PHOTOS_DIR
    elif media == 'home':
      return NAS_HOME_DIR  
    else:
      raise ValueError( f"unknown media {media} for {ctx}" )
  elif ctx == 'nas-to-veracrypt' :
    if media == 'photos':
      return VERACRYPT_PHOTOS_DIR
    else:
      raise ValueError( f"unknown media {media} for {ctx}" )
  elif ctx == 'nas-to-hd' :
    if media =='music':
      return HD_MUSIC_DIR
    elif media == 'videos':
      return HD_VIDEOS_DIR
    elif media == 'photos':
      return HD_PHOTOS_DIR
    elif media == 'home':
      return HD_HOME_DIR  
    elif media == 'homes' :
      return HD_HOMES_DIR
    else:
      raise ValueError( f"unknown media {media} for {ctx}" )
  else:
    raise ValueError( f"unknown ctx {ctx}" )


def open_rsync( dry_run:bool=True ):
  """ starts the rsync command 

  The motivation fo rsuch command is to provide the ability to make 
  some filetring associated to context or media.
  """

  if dry_run is True:
    cmd = 'rsync -avzhce ssh  --dry-run  --progress'
  else:
    cmd = 'rsync -avzhce ssh  --progress'
  return cmd

def close_rsync( cmd:str, log_file=None ):
  """ if dry_run is request redirect command output in log file

  In order to run different command in parallel, the crc32 of the command
  is appended to the LOG_FILE.
  """

  if log_file is not None:
    cmd += f" >> {log_file} "
  print( f"Executing {cmd}\n" )
  return cmd


def rsync_home( ctx:str, dry_run:bool=True, log_file=None ):
  """ return the corresponding rsync command for the media 'home'

  The media 'home' rrequires some filtering as to prevent 
  backing-up all cache files as well as files we do not need to backup.

     rsync -avzhce ssh  --dry-run  --progress --include '.ssh' --include '.thunderbird' --exclude '/.*' --exclude '*.swp' --exclude '*.swo' --exclude '*.swm' --exclude '*$py.class' --exclude '*.pyc' --exclude '*.pyo' --exclude '*.pyd' --exclude '.pylintrc' --exclude '.ipynb_checkpoints/' --exclude '__pycache__/' --exclude '.DS_Store' --exclude '*.aux' --exclude '*.blg' --exclude '*.log' --exclude '*.out' --exclude '*.bbl' --exclude 'gems' --exclude 'gopath' --exclude 'gitlab/archive' --exclude '2012_09_26-PhD-daniel-migault' --exclude 'bkp-nas' --exclude 'Downloads' --exclude 'snap' --exclude 'Pictures' --exclude 'Videos' --exclude 'myVideos' --exclude 'myPhotos' --exclude 'myMusic' /home/emigdan/ dan@nas.local:/volume1/homes/dan/work/ericsson/emigdan
  """
  cmd = open_rsync( dry_run )
  for i in INCLUDE:
    cmd += f" --include '{i}'"
#  for i in [ DESKTOP_MUSIC_DIR, DESKTOP_VIDEOS_DIR, \
#             DESKTOP_PHOTOS_DIR, DESKTOP_HOME_DIR ]:
  ## we exclude the media 'music', 'photos' and 'videos'
  ## The current definition is hardcoded.
  ## Considering the full path does not produces a match
  ## as a result we only take the stem. 
  ## we shoudl write that from the configuration parameters 
  ## instead of hard coding it.
  for i in [ 'myMusic', 'myVideos', 'myPhotos', ]:  
    EXCLUDE.append( i )
  for i in EXCLUDE:
    cmd += f" --exclude '{i}'"
#  cmd += f" {DESKTOP_HOME_DIR} {NAS_HOME_DIR}"
  cmd += f" {src( ctx, 'home' )} {dst( ctx, 'home' )}"
  return close_rsync( cmd, log_file )

def rsync( ctx:str, media:str, dry_run:bool=True, log_file=None ):
  """returns the rsync cli """

  if media == 'home' : 
    return rsync_home( ctx, dry_run=dry_run, log_file=log_file ) 
  elif media in [ 'photos', 'videos', 'music', 'homes' ]:
    cmd = open_rsync( dry_run )
    cmd += f" {src( ctx, media )} {dst( ctx, media )}"
    return close_rsync( cmd, log_file )
  else:
    raise ValueError( f"unknown media {media}" )

##def rsync_photos( dry_run:bool=True, ctx:str='desktop-to-nas' ):
##  """
##   rsync -avzhce ssh --dry-run --progress  /home/emigdan/myPhotos/ dan@nas.local:/volume1/homes/dan/myPhotos/
##
##  """
##  cmd = open_rsync( dry_run )
###  cmd += f" {DESKTOP_PHOTOS_DIR} {NAS_PHOTOS_DIR}"
##  cmd += f" {local( ctx, 'photos' )} {remote( ctx, 'photos' )}"
##  return close_rsync( cmd, dry_run, 'photos' )
##   
##def rsync_music( dry_run:bool=True ):
##  """
##   rsync -avzhce ssh --dry-run --progress /home/emigdan/myMusic/   dan@nas.local:/volume1/homes/dan/music/myMusic/ 
##
##  """
##  cmd = open_rsync( dry_run )
##  cmd += f" {local( ctx, 'music' )} {remote( ctx, 'music' )}"
###  cmd += f" {DESKTOP_MUSIC_DIR} {NAS_MUSIC_DIR}"
##  return close_rsync( cmd, dry_run, 'music' )
##
##def rsync_videos( dry_run:bool=True ):
##  """
##  rsync -avzhce ssh --dry-run --progress /home/emigdan/myVideos/   dan@nas.local:/volume1/homes/dan/myVideos/
##
##  """
##  cmd = open_rsync( dry_run )
##  cmd += f" {DESKTOP_VIDEOS_DIR} {NAS_VIDEOS_DIR}"
##  return close_rsync( cmd, dry_run, 'videos' )
##



def cli( ctx=None ):    
  description = f"""{ctx} Backup
  
  To perform a full backup: backup
  To check before performing a full back: backup --dry_run
  To perform a backup of (photos/videos/videos/user): backup --photos
  """
  parser = argparse.ArgumentParser( description=description )
  parser.add_argument( '-dry_run', '--dry_run', default=False,  \
  action='store_const', const=True, \
  help="Perform a dry run " )
  parser.add_argument( '-home', '--home', default=None,  \
  action='store_const', const=True, \
  help="Only performs User Space backup" )
  parser.add_argument( '-photos', '--photos', default=None,  \
  action='store_const', const=True, \
  help="Only performs Photos backup" )
  parser.add_argument( '-music', '--music', default=None,  \
  action='store_const', const=True, \
  help="Only performs Music backup" )
  parser.add_argument( '-videos', '--videos', default=None,  \
  action='store_const', const=True, \
  help="Only performs Videos backup" )
  parser.add_argument( '-homes', '--homes', default=None,  \
  action='store_const', const=True, \
  help="Only performs Full NAS backup" )
  parser.add_argument( '-view_log', '--view_log', default=None,  \
  action='store_const', const=True, \
  help="Display the last log" )
  args = parser.parse_args()

  if args.photos is True:
    media = 'photos'
  elif args.videos is True:
    media = 'videos'
  elif args.home is True:
    media = 'home'
  elif args.music is True:
    media = 'music'
  elif args.homes is True:
    media = 'homes'
  else: 
    raise ValueError( "Please specify media with --photos or " +\
                        "--videos or --home or --music" )

  log_file = f"{LOG_FILE}.{ctx}.{media}"  
  if args.view_log is True:
    ## checking we have defined the backup we want to view  
    if [args.photos, args.videos, args.home, args.music ].count( True ) != 1:
      raise ValueError ( "Please specify the log you want to display with" +\
                         "--photos or --videos or --home or --music " )    
    subprocess.run( f"vim {log_file}", shell=True )
  else:
    if args.dry_run is False:
      print( "WARNING! Be sure you want to perform your backup!" )
      print( "if you are unsure, please consider the --dry_run\n" )
      log_file = None
    else:  
      ## creating an empty log file.
      ## the log_file is used during the dry_run only.
      with open( log_file, 'wt' ) as f:
        pass
    
    ## select if only one type of backup needs to be performed
    subprocess.run( f"{rsync( ctx, media, args.dry_run, log_file )}", shell=True )
        
    if args.dry_run is True:
      print( "To visualize the changes, please add '--view_log'")

def backup_desktop( ):
  """ backup Desktop to NAS """
  cli( ctx='desktop-to-nas' )    

def backup_nas_veracrypt( ):
  """ backup NAS to a Veracrypt HD

  Only the photos are backup - due to space.
  """

  print( "Checking existence of directories:" ) 
  if os.path.exists( VERACRYPT_PHOTOS_DIR ) is False:
    msg = "  - Unable to back-up the NAS/Photos to VERACRYPT: " +\
          f"cannot find {VERACRYPT_PHOTOS_DIR}."
    raise ValueError( msg )
  else:
    print( f"{VERACRYPT_PHOTOS_DIR} properly detected" )
  print( "" )
  cli( ctx='nas-to-veracrypt' )    

def backup_nas_hd( ):
  """ backup NAS to a unencrypted HD """

  print( "Checking existence of directories:" ) 
  for d in [ HD_HOMES_DIR, HD_VIDEOS_DIR, HD_HOME_DIR, HD_MUSIC_DIR ]:
    if os.path.exists( d ) is False:
      msg = "  - Unable to back-up the NAS to HD: " +\
            f"cannot find {d}."
      raise ValueError( msg )
    else: 
      print( f"  - {d} properly detected" )
  print( "" )
  cli( ctx='nas-to-hd' )    

if __name__ == '__main__' :
  backup_nas_hd( ) 
      
