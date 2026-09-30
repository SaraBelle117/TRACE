https://www.labgym.org/ <-- Open source animal analysis framework

# How to run this binch
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
run this in ur terminal, open vscode or whatever IDE that supports jupyter notebook, and just run through each cell. 
The final cell shows the before and after of bounding box placements on a full image, and ./out contains both
the annotated video, as well as a csv with each bounding box indexed by frame.



MEETING NOTES (SAMMY):

So far what I have is a start on tracking and skeletonizing worms in photos and videos. The code is in pretty rough shape and not well documented, but I wanted to get a stronger idea of what the first steps might look like before I got to far in programming. 

I used the WORM_MOTEL demo video, which Zevan found under TierpsyTracker's example data, which shows 4 square dishes in a grid pattern, each containing one worm. The images are greyscale and have some hairs, obstructions, e.t.c.. 

I have a jupyter notebook which can analyze a photo, or equivalently a frame of a video. The program identifies 'structures' that share a similar pixel color value, and uses skikit images morphology library to skeletonize the structures, using a thinning algorithm that slowly removes color value from all pixels, until the edges of shape fade out leaving only a skelton of a given pixel width. An object that is too thin, or too large, is excluded. The function works pretty well, only mistakenly adding additional bounding boxes occasionally, and never missing a bounding box. Then, I used scikit images morphology module, to create a skeleton for each worm. Direction is not yet identified, but each frame/photo is outputed with it's annotated skeleton and bounding box. From what I've read so far, thinning algorithms are not the ideal approach becuase coiled worms can cause issues in detection, however the conversion to a convolutional network based approach like worm pose is easy. Since each worm can be extracted into a smaller sub image from it's bounding box with the code we have, we pass that cleaner subimage into the open source tool wormpose, to track centerline, length, curvature, and posture across time. I also then save the bounding box annotations frame by frame to a csv file for later.

Goals for the next week that would be very useful in my mind:
- Identify useful 'features' from hdf5 files / explore more about what hdf5 files do
    - Try using tierpsy trackers to start gather that information
    - find a unique signature for each worm? 
        - the issue is when worms get close to one another, they overlap in tierpsy tracker / get mixed up 
        - there needs to be a way of identifying particular worms over time
- research alternatives to tierpsy tracker, what we would have to work on in order to make it work

- cleaning up and documenting code, crop images of worms across time into one video per worm as well?
    - can easily crop images of worms


I will use what I have, put it through tierpys automagically, probably, is the easy option, and then do analysis of the output features


basically, does open worm analyis let us just take the hdf5 file?


Functions

    1. Takes in a frame                                                 bounding boxes of potential worms based on given parameters
    2. Takes in a set of bounding boxes                                 remove some from the set based on different criteria
    3. Takes in a frame and bounding boxes                              returns cropped images of those bounding boxes
    4. Takes in cropped worm image                                      returns hdf5 data on them using worm analysis toolbox
    5. Take in a group of cropped worm images (same worm across time)   











    

theye use tierpsy tracker > hdf5 files > csv > change over titem
.hdf5 files have features??


features that can be tracked from tierpsy:
- xy coordinates
- area
- perimeter
- solidity
- compactness

- threshold
- timestamp
- worm index joining
- swimming behavior!!! BODY SIZE CHANGES!!!
- frequency and also forward and backward speed

- frequency and also forward and backward speed
- TIMESTAMPED rupture events
- plots for worms and groups of worms

- user manual and isntallation instruction
- annotated datasets and benchmarks

Worms and Torture
- Any particularly good resources in C. elegans and current research?
- What are the sources of stress? Will the experimentation be mostly surrounding “exposure to hypertonic or hypotonic environments” like the description mentions? 
- Are there other variables that we will explore?

Data
- What resources do we have at our disposal? 
- Will we be working with physical samples or just using preexisting data?
- How is this data being sourced?
- Will we primarily work with images, pre-recorded videos, or live video?
- What hardware might be used to capture or stream data? 
- Are there any other requirements for data that our program must be able to manipulate?

Computation 
- Should this software run locally or use a client-server model?
- Is there a maximum amount of time that the pipeline should take to complete a pass/perform analysis?
- What operating system requirements are there for the software?
- Any special security considerations?

FEATURES:
- What can be improved upon from the software that currently exists? 
- Are there any new features that we should consider?
- What specific needs do you have that you believe will be particularly challenging for us to work with?
- Do you have a recommendation for splitting work between us?

