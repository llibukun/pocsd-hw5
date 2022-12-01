# Layiwola Ibukun
# Tashfique Choudhury

# POCSD - EEL5737 Principles of Computer System Design
# Homework 5 - RAID 5 Server Model
# Due: Friday, December 2nd, 2022
# memoryfs_server.py

import pickle, logging
import argparse
import time
import dbm
import os.path
import hashlib # checksums

# For locks: RSM_UNLOCKED=0 , RSM_LOCKED=1 
RSM_UNLOCKED = bytearray(b'\x00') * 1
RSM_LOCKED = bytearray(b'\x01') * 1

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
  rpc_paths = ('/RPC2',)

class DiskBlocks():
  def __init__(self, total_num_blocks, block_size):
    # This class stores the raw block array
    self.block = []  
    # This stores the checksum for each block
    self.checksum = {}  

    # Initialize raw blocks 
    for i in range (0, total_num_blocks):
      putdata = bytearray(block_size)
      self.block.insert(i,putdata)
      self.checksum[i] = hashlib.md5(putdata)


if __name__ == "__main__":

  # Construct the argument parser
  ap = argparse.ArgumentParser()

  ap.add_argument('-nb', '--total_num_blocks', type=int, help='an integer value')
  ap.add_argument('-bs', '--block_size', type=int, help='an integer value')
  ap.add_argument('-port', '--port', type=int, help='an integer value')
  ap.add_argument('-cblk', '--cblk', default=-1, type=int, help='an integer value')

  args = ap.parse_args()

  if args.total_num_blocks:
    TOTAL_NUM_BLOCKS = args.total_num_blocks
  else:
    print('Must specify total number of blocks') 
    quit()

  if args.block_size:
    BLOCK_SIZE = args.block_size
  else:
    print('Must specify block size')
    quit()

  if args.port:
    PORT = args.port
  else:
    print('Must specify port number')
    quit()

  if args.cblk:
    CORRUPT_BLOCK = args.cblk

  # initialize blocks
  RawBlocks = DiskBlocks(TOTAL_NUM_BLOCKS, BLOCK_SIZE)

  # Create server
  server = SimpleXMLRPCServer(("127.0.0.1", PORT), requestHandler=RequestHandler) 

  def Get(block_number):
    # emulated data decay
    if block_number == CORRUPT_BLOCK:
      RawBlocks.block[block_number][:4] = bytearray(b'\xFF\x00\xF0\x0F')

    result = RawBlocks.block[block_number]
    # compare checksums
    if RawBlocks.checksum[block_number].hexdigest() == hashlib.md5(result).hexdigest():
      return result

    # checksum error
    return -1

  server.register_function(Get)

  def Put(block_number, data):
    # store data and checksum
    RawBlocks.block[block_number] = data.data
    RawBlocks.checksum[block_number] = hashlib.md5(data.data)

    return 0

  server.register_function(Put)

  def RSM(block_number):
    # Get the RSM Block
    result = RawBlocks.block[block_number]

    # compare checksums
    if RawBlocks.checksum[block_number].hexdigest() == hashlib.md5(result).hexdigest(): 
      RawBlocks.block[block_number] = bytearray(RSM_LOCKED.ljust(BLOCK_SIZE,b'\x01'))
      RawBlocks.checksum[block_number] = hashlib.md5(bytearray(RSM_LOCKED.ljust(BLOCK_SIZE,b'\x01')))
      return result

    # checksum error
    return -1

  server.register_function(RSM)

  # Run the server's main loop
  print ("Running block server with nb=" + str(TOTAL_NUM_BLOCKS) + ", bs=" + str(BLOCK_SIZE) + " on port " + str(PORT))
  server.serve_forever()

