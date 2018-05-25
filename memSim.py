import argparse
from collections import OrderedDict

tlb = OrderedDict()
pageTable = [None] * 256
backingStore = open("BACKING_STORE.bin", 'r')

def checkNumFrames(input):
    numFrames = int(input)
    if numFrames <= 0 or numFrames > 256:
        raise argparse.ArgumentTypeError("%s is an invalid value for number of frames. "
                                         "Please enter a number between 1 and 256." % numFrames)
    return numFrames

def checkPRA(PRA):
    if PRA == "FIFO" or PRA == "LRU" or PRA == "OPT":
        return PRA
    else:
        raise argparse.ArgumentTypeError("%s is an invalid value for the Page Replacement Algorithm. "
                                         "Please enter 'FIFO', 'LRU', or 'OPT'." % PRA)

def TLBLookup(pageNum):
    if pageNum in tlb:
        frame = tlb[pageNum]
        del tlb[pageNum]
        tlb[pageNum] = frame
        return frame
    else:
        return None

def insertTLB(pageNum, frame):
    if len(tlb) == 16:
        tlb.popitem(last=False)
    tlb[pageNum] = frame

def PTLookup(pageNum):
    frame = pageTable[pageNum]
    if frame is not None:
        insertTLB(pageNum, frame)
    return frame

def memSim():
    # Parse Arguments
    parser = argparse.ArgumentParser(description="A virtual memory simulator.")
    parser.add_argument("sequenceFilePath", help="File containing the list of logical memory addresses.")
    parser.add_argument("frames", nargs="?", default=256, type=checkNumFrames, help="Number of frames in the system.")
    parser.add_argument("PRA", nargs="?", default="FIFO", type=checkPRA, help="Page Replacement Algorithm.")
    args = parser.parse_args()
    numFrames = args.frames
    pra = args.PRA
    RAM = [None] * numFrames
    frameCursor = 0
    pageFaults = 0
    tlbHits = 0
    tlbMisses = 0

    # Store addresses into data structure
    with open(args.sequenceFilePath, 'r') as sequenceFile:
        addresses = []
        for line in sequenceFile:
            address = line.strip('\n')
            addresses.append(int(address))
        sequenceFile.close()

    for address in addresses:
        # get PageNum and offset
        binary = format(address, '016b')
        pageNum = int(binary[0:8], 2)
        offset = int(binary[8:], 2)

        # Lookup page in TLB
        frame = TLBLookup(pageNum)

        if frame is None:
            # Lookup page in Page Table
            frame = PTLookup(pageNum)
            tlbMisses += 1
        else:
            tlbHits += 1

        if frame is None:
            # Hard Miss - Look up in Backing Store
            backingStore.seek(pageNum * 256)
            data = backingStore.read(256)
            # Update pageTable and TLB
            pageTable[pageNum] = frameCursor
            insertTLB(pageNum, frameCursor)
            # insert data into RAM using frameCursor as key
            RAM[frameCursor] = data
            referenceByte = ord(data[offset])
            if referenceByte > 127:
                referenceByte = (256-referenceByte) * -1
            print str(address) + ", " + str(referenceByte) + ", " + str(frameCursor) + ", " + ''.join(["%02X" % ord(x) for x in data]).strip()
            pageFaults += 1
            frameCursor = (frameCursor + 1) % (numFrames - 1)
    print "Number of Translated Addresses = " + str(len(addresses))
    print "Page Faults = " + str(pageFaults)
    print "Page Fault Rate = %.3f" % float(pageFaults / len(addresses))
    print "TLB Hits = " + str(tlbHits)
    print "TLB Misses = " + str(tlbMisses)
    print "TLB Hit Rate = %.3f" % float(tlbHits / len(addresses))


    backingStore.close()

if __name__ == '__main__':
    memSim()