# UltraSplitter 1.0 made by vik - 2012 - v@42.am
#
# Tool to convert a .KRO file to a DZI (Deep Zoom Image) format (dir + xml)
# Usage: ./script [image.kro]
#
# Format desc: take a look at http://www.gasi.ch/blog/inside-deep-zoom-2/
#
# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.
#
# Tested functionnal on 64bits win7 with 64bits python 2.7 and 64bits PIL library
# needs PIL (python image library)

import sys, os, Image, struct, math
from struct import *

tile_size = 256

def die(error_message = ''):
  print(error_message)
  if os.name == 'nt':
    raw_input("Press ENTER to exit")
  sys.exit(0)

if len(sys.argv) == 1:
  die("Usage: script [.kro file]")

filename = sys.argv[1]

try:
  f = open(filename, 'rb')
except:
  die('ERROR: absolute filepath needed ! (or other error)')

header = unpack_from('>3sb4L', f.read(20))

if header[0] != 'KRO':
  die("'"+filename+"' is not a KRO file ! (eh ouais)")

size_index = header[4]*header[5]/8   # example: 4 = 8bpp * 4layers / 8bits per octet

print '\n%s file, version %s -- X:%d Y:%d %d bpp per layer with %d layers' % header
print 'approx memory needed : '+str(header[2]*tile_size*size_index/1024/1024+10)+' mo =)' 

infofile = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><Image TileSize=\"%d\" Overlap=\"1\" Format=\"jpg\" xmlns=\"http://schemas.microsoft.com/deepzoom/2008\"><Size Width=\"%d\" Height=\"%d\"/></Image>" % (tile_size, header[2], header[3])
f_i = open(filename[:-4]+'.xml', 'w')
f_i.write(infofile)
f_i.close()

if header[5] == 4:
  img_format = 'RGBA'
elif header[5] == 3:
  img_format = 'RGB'

if header[2] >= header[3]:
  levelmax = math.log(header[2], 2)
else:
  levelmax = math.log(header[3], 2)
levelmax = int(math.ceil(levelmax))

print 'max zoom level is :',levelmax
tile_y = 0
y_max = header[3]-tile_size

try:
  os.makedirs(os.path.join(os.path.abspath(filename[:-4])+'_files', str(levelmax)))
except:
  pass
print '\nMaking biggest tiled image:\n0%',
  
for y in range(0, header[3], tile_size):
  if y > 0:
    print str(y*100/header[3])+'%',
  if y+tile_size < header[3]:
    imgdata = f.read(size_index*header[2]*tile_size)
    imgmap = Image.frombuffer(img_format,(header[2],tile_size),imgdata,'raw',img_format,0,1)
    cur_height = tile_size
  else:
    imgdata = f.read(size_index*header[2]*(header[3]-y))
    imgmap = Image.frombuffer(img_format,(header[2],header[3]-y),imgdata,'raw',img_format,0,1)
    cur_height = header[3]-y  

  tile_x = 0
  x_max = header[2]-tile_size
  for x in range(0, header[2], tile_size):
    if x+tile_size < header[2]:
      tile = imgmap.crop((x,0,x+tile_size,cur_height)) #box = left up right down  
    else:
      tile = imgmap.crop((x,0,header[2],cur_height)) #box = left up right down
    cur_tile_path = os.path.join(os.path.abspath(filename[:-4])+'_files', str(levelmax), str(tile_x)+"_"+str(tile_y)+".jpg")      
    tile.save(cur_tile_path,"JPEG")
    tile_x += 1
  tile_y += 1

f.close()

print '100%\n\nMaking other zoom levels:',
      
for level in range (levelmax-1, 0, -1):
  print "\n\nLevel "+str(level)+"\n0%",
  src_path = os.path.join(os.path.abspath(filename[:-4])+'_files', str(level+1))
  x_max = tile_x-1
  y_max = tile_y-1
  try:
    os.mkdir(os.path.join(os.path.abspath(filename[:-4])+'_files', str(level)))
  except:
    pass
  tile_y = 0
  for y in range(0, y_max+1, 2):
    tile_x = 0
    if y > 0:
      print str(y*100/(y_max+1))+'%',
    for x in range(0, x_max+1, 2):
      if y != y_max and x != x_max:
        tile_00 = Image.open(os.path.join(src_path, '%d_%d.jpg' % (x, y)))
        tile_10 = Image.open(os.path.join(src_path, '%d_%d.jpg' % (x+1, y)))
        tile_01 = Image.open(os.path.join(src_path, '%d_%d.jpg' % (x, y+1)))
        tile_11 = Image.open(os.path.join(src_path, '%d_%d.jpg' % (x+1, y+1)))
        new_tile = Image.new(img_format, ((tile_00.size[0]+tile_10.size[0]),(tile_00.size[1]+tile_01.size[1])))
        new_tile.paste(tile_00, (0,0))
        new_tile.paste(tile_10, (tile_00.size[0],0))
        new_tile.paste(tile_01, (0,tile_00.size[1]))
        new_tile.paste(tile_11, (tile_00.size[0],tile_00.size[1]))
      
      elif y == y_max and x != x_max:
        tile_00 = Image.open(os.path.join(src_path, '%d_%d.jpg' % (x, y)))
        tile_10 = Image.open(os.path.join(src_path, '%d_%d.jpg' % (x+1, y)))
        new_tile = Image.new(img_format, (tile_00.size[0]+tile_10.size[0], tile_00.size[1]))
        new_tile.paste(tile_00, (0,0))
        new_tile.paste(tile_10, (tile_00.size[0],0))
       
      elif x == x_max and y != y_max:
        tile_00 = Image.open(os.path.join(src_path, '%d_%d.jpg' % (x, y)))
        tile_01 = Image.open(os.path.join(src_path, '%d_%d.jpg' % (x, y+1)))
        new_tile = Image.new(img_format, (tile_00.size[0], tile_00.size[1]+tile_01.size[1]))
        new_tile.paste(tile_00, (0,0))
        new_tile.paste(tile_01, (0,tile_00.size[1]))

      elif y == y_max and x == x_max:
        new_tile = Image.open(os.path.join(src_path, '%d_%d.jpg' % (x, y)))
      
      new_tile_size_x = int(math.ceil(new_tile.size[0]/2))
      new_tile_size_y = int(math.ceil(new_tile.size[1]/2))
      if new_tile.size[0] == 1: # prevents to go under 1 px width
        new_tile_size_x = 1
      if new_tile.size[1] == 1: # and height
        new_tile_size_y = 1
      
      new_tile = new_tile.resize((new_tile_size_x, new_tile_size_y), Image.BILINEAR) # or BICUBIC
      cur_tile_path = os.path.join(os.path.abspath(filename[:-4])+'_files', str(level), str(tile_x)+"_"+str(tile_y)+".jpg")
      new_tile.save(cur_tile_path, "JPEG")
            
      tile_x += 1
    tile_y += 1  
  print '100%',

die('\n\nTHE END !')

