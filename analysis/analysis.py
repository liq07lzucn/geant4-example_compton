
""" Basic analysis code for Geant4 simulation """

import os,sys
import numpy as np
import matplotlib.pylab as plt
import glob

# Geant4 output data format 
geant4_dtype = np.dtype([("event",np.int),  # beam number 
                         ("module",np.int), # module (granma) copy no.
                         ("box",np.int),    # box (mother) copy no.
                         ("voxel",np.int),  # voxel (person) copy np.
                         ("edep",np.float), # energy deposition [MeV]
                         ("posx",np.float), # position x [mm]
                         ("posy",np.float), # position y [mm]
                         ("posz",np.float), # position z [mm]
                         ("time",np.float), # time [ns] (time after beam generated)
                         ("track",np.int),  # track id (the order of interaction process)
                         ("particle",np.int)]) # particle id (interacted particle)


def imaging(data,eth,DEBUG=False):

    # energy-threthold cut
    mask = data["edep"]>=eth
    data = data[mask]
    
    voxel = np.arange(25*25+1)
    voxel.astype(int)
    y = np.histogram(data["voxel"],bins=voxel)[0]
    map_= y.reshape((25,25))
    
    if DEBUG==True:
        plt.figure()
        plt.pcolor(map_)
        plt.colorbar()
        plt.savefig("heatmap.png")
        plt.show()

    mask = y>np.max(y)/2.
    voxel = voxel[:-1][mask]
    #voxel = voxel[:-1]
    posx = (voxel[:-1]%25-12.5)*2.+1.
    posy = (voxel[:-1]//25-12.5)*2.+1.
    #print(posx)
    #print(posy)

    posz = np.sin(np.arccos(posy/24.0))*24.0
    #idx_source = np.argmax(np.square(posx)+np.square(51.6-posz))
    idx_source = np.argmax(np.square(posx)+np.square(posy))

    print("voxel no %d: (%.1f,%.1f,%.1f)"%(voxel[idx_source],posx[idx_source],posy[idx_source],posz[idx_source]))

    return voxel[idx_source],posx[idx_source],posy[idx_source],posz[idx_source]

def check_sourcepos(dirname,outfil="pos.info",DEBUG=True):

    fil = open(dirname+"/"+outfil,"r")
    xs=[]
    ys=[]
    zs=[]
    for i,line in enumerate(fil):
        if i==0:
            print(line)
            continue
        else:
            head,x,y,z,unit = line.split()
            xs.append(float(x))
            ys.append(float(y))
            zs.append(float(z))

    if DEBUG:
        from mpl_toolkits.mplot3d import Axes3D
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(xs, ys, zs)
        ax.set_xlabel('X [mm]')
        ax.set_ylabel('Y [mm]')
        ax.set_zlabel('Z [mm]')
        plt.show()

    return np.array(xs),np.array(ys),np.array(zs)

def calc_cf_with_pos(data,eth,beam_no,posx,posy,posz,xs,ys):
                     
    # energy-threthold cut
    mask = data["edep"]>=eth
    data_eth = data[mask]

    #data_posx = (data["voxel"]%25-12.5)*2.+1.
    #data_posy = (data["voxel"]//25-12.5)*2.+1.

def calc_cf_known_pos(filnames,xs,ys,eth,beam_no,DEBUG=True):

    cfs = np.zeros(len(filnames))
    for i,filname in enumerate(filnames):
        data = np.load(filname)
        cfs[i] = calc_cf(data,eth,beam_no)
    
    if DEBUG:
        plt.figure()
        plt.scatter(xs,ys,cfs)

    return cfs

def calc_cf(data,eth,beam_no):

    # energy-threthold cut
    mask = data["edep"]>=eth
    data_eth = data[mask] 
    # remove coincidence events
    detect_no = len(np.unique(data_eth)) 

    cf = beam_no*1.0/(detect_no*1.0) #cf = bq/cps   

    return cf

def main():

    filname1 = sys.argv[1] # import npy
    filname2 = sys.argv[2] # import npy
    randdir = sys.argv[3] # data
    beam_no = 1e+8 # sys.argv[3]
    eth  = 0 # sys.argv[4]

    xs,ys,zs = check_sourcepos(dirname=sys.argv[3],outfil="pos.info",DEBUG=True)

    print("mean cf")
    data = np.load(filname1)
    cf_main1 = calc_cf(data,eth=eth,beam_no=1e+8)

    data = np.load(filname2)
    cf_main2 = calc_cf(data,eth=eth,beam_no=1e+8)

    print(cf_main1)
    print(cf_main2)
    
    filnames = glob.glob(randdir+"/*.npy")
    print("%d files found"%len(filnames))
    
    
    cfs = np.zeros(len(filnames))
    for i,filname in enumerate(filnames):
        
        data = np.load(filname)
        cfs[i] = calc_cf(data,eth,1e+6)
    
    cfs_img = np.zeros(len(filnames))
    for i,filname in enumerate(filnames):
        
        data = np.load(filname)
        #plt.figure()
        #plt.scatter(data["posx"],data["posz"],label="x-z")
        #plt.scatter(data["posy"],data["posz"],label="y-z")
        #plt.show()
        #check_geometry(data)
        voxel,posx,posy,posz = imaging(data,eth=0,DEBUG=True)
        idx_pos = np.argmin(np.square(xs-posx)+np.square(ys-posy))
        cds_img = cfs[idx_pos]
        #if i==5: break

    plt.figure()
    plt.axhline(cf_main1,color="r",linestyle="dashed",label="monte calro")
    plt.axhline(cf_main2,color="b",linestyle="dashed",label="gakkai")
    plt.plot(cfs,"k.")
    plt.plot(cfs_img,"ko")
    plt.legend()


    plt.figure()
    #plt.plot(cf_main1/cfs,"r.",label="monte calro rand") 
    plt.plot(np.max(cfs)/cfs,"g.",label="monte calro")
    plt.plot(cf_main2/cfs,"b.",label="gakkai")
    plt.plot(cfs/cfs,"k",label="ideal")
    plt.plot(cfs_img/cfs,"gray",label="imaging")
    plt.yscale("log")
    plt.legend()
    plt.show()

if __name__=='__main__':
    main()
    sys.exit("Fin: geant4 simulation analysis!")
