import argparse
from collections import OrderedDict

tlb = OrderedDict()
pageTable = [None] * 256
backingStore = open("BACKING_STORE.bin", 'r')
ramOrder = OrderedDict()


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


def getNextFrame(frameCursor, algorithm, RAM, numFrames):
    # Get number of entries in RAM
    numRAMEntries = 0
    for entry in RAM:
        if entry is not None:
            numRAMEntries += 1

    #Check to see if RAM is full
    if numRAMEntries < numFrames or algorithm == "FIFO":
        return (frameCursor + 1) % numFrames
    elif algorithm == "LRU":
        # TODO: Be better.
        leastUsed = ramOrder.popitem(last=False)
        return leastUsed[0]
    else:
        print "OPT"


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
            print "TLB Miss"
        else:
            print "TLB Hit"
            tlbHits += 1

        if frame is None:
            print "Page Fault"
            # Hard Miss - Look up in Backing Store
            backingStore.seek(pageNum * 256)
            data = backingStore.read(256)

            prevData = RAM[frameCursor]
            # If RAM has preexisiting data,
            if prevData is not None:
                # Erase old frame from PageTable entry
                for pNum, frameEntry in enumerate(pageTable):
                    if frameEntry == frameCursor:
                        pageTable[pNum] = None

            # insert data into RAM using frameCursor as key
            RAM[frameCursor] = data

            # Update pageTable and TLB
            frame = frameCursor
            pageTable[pageNum] = frameCursor
            insertTLB(pageNum, frameCursor)
            pageFaults += 1
        else:
            # Get Data from RAM
            data = RAM[frame]

        # LRU: Update order of RAM access
        if pra == "LRU":
            if frame in ramOrder:
                del ramOrder[frame]
            ramOrder[frame] = 0

        # Get value of the referenced byte
        referenceByte = ord(data[offset])
        # Make it signed
        if referenceByte > 127:
            referenceByte = (256-referenceByte) * -1

        # Output
        print str(address) + ", " + str(referenceByte) + ", " + str(frame) + ", " \
              + ''.join(["%02X" % ord(x) for x in data]).strip()

        # Get next frame
        frameCursor = getNextFrame(frameCursor, pra, RAM, numFrames)

    print "Number of Translated Addresses = " + str(len(addresses))
    print "Page Faults = " + str(pageFaults)
    print "Page Fault Rate = %.3f" % (float(pageFaults) / float(len(addresses)))
    print "TLB Hits = " + str(tlbHits)
    print "TLB Misses = " + str(tlbMisses)
    print "TLB Hit Rate = %.3f" % (float(tlbHits) / float(len(addresses)))


    backingStore.close()

if __name__ == '__main__':
    memSim()