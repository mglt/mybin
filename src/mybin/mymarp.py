#!/usr/bin/python3
#import os
import argparse
import subprocess
import pathlib

def marp_to_html( md_file ):
  """ command line to generate an html file """

  cmd =  """docker run -u "node" --rm --init -v $PWD:/home/marp/app/ -e LANG=$LANG -p 37717:37717 marpteam/marp-cli -w --html --allow-local-files """
  return f"{cmd} {md_file}"

def marp_to_pdf( md_file ):
  """ command line to generate an pdf file """

  cmd = """docker run --rm -v $PWD:/home/marp/app/ -e LANG=$LANG -e MARP_USER="$(id -u):$(id -g)" marpteam/marp-cli -w --html --pdf --allow-local-files"""
  return f"{cmd} {md_file}"

def marp_to_ppt( md_file ):
  """ command line to generate an ppt file """

  cmd = """docker run -u "node" --rm --init -v $PWD:/home/marp/app/ -e LANG=$LANG -p 37717:37717 marpteam/marp-cli -w --html --pptx --allow-local-files"""
  return f"{cmd} {md_file}"

#def output_file( md_file, suffix ):
#  """returns the corresponding output file """
#
#  return PurePath( md_file ).with_suffix( suffix )
#  file_name = os.path.basename( md_file )
#  file = os.path.splitext( file_name )
   


def cli():

  description = """Convert markdown presentation using marp"""
  parser = argparse.ArgumentParser( description=description )
  parser.add_argument('md_file', type=pathlib.Path )
  parser.add_argument( '-pdf', '--pdf', default=False,  \
  action='store_const', const=True, \
  help="generates a PDF output" )
  parser.add_argument( '-pptx', '--pptx', default=False,  \
  action='store_const', const=True, \
  help="generates a PPTx output" )
  parser.add_argument( '-html', '--html', default=False,  \
  action='store_const', const=True, \
  help="generates an HTML output" )
  args = parser.parse_args()

  print( f"DEBUG args : {args} " )
  if [ args.pdf, args.pptx, args.html ].count( True ) == 0:
    args.pdf = True
  elif [ args.pdf, args.pptx, args.html ].count( True ) > 1:
    raise ValueError( f"Please select a single output format" )      


  
  if args.pdf is True:
    subprocess.run( marp_to_pdf( args.md_file ), shell=True, start_new_session=True )
    ## TODO: 1. run subprocess in the background
    ##       2. enable to kill marp containers
    pdf = pathlib.PurePath( args.md_file ).with_suffix( '.pdf' )
    print( f"DEBUG: pdf : {pdf}" )
    subprocess.run( f"okular {pdf}", shell=True )

  elif args.pptx is True: 
    marp_to_pptx( args.md_file )
  elif args.html is True: 
    marp_to_html( args.md_file )
  subprocess.run( f"vim {args.md_file}", shell=True )
     
if __name__ == '__main__':
  cli()    
