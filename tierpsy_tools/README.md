# Tierpsy Tool

We have compiled the requested outputs into a python script which allows you to process a video alongside it's tierpsy tracker output data to generate csvs, and an annotated first frame.

The instructional video, tierpsy_tools_instructions.mov, gives a more in depth process on how to use the tool, but here's the basic idea:

1. Open a terminal inside of this folder
2. Run the setup_venv.sh script if you are on mac, or use the setup_venv.bat script if you are on windows.
3. Copy the command at the end of the scipts output into your terminal and hit enter ('source .venv/bin/activate')
4. type 'spyder' into your terminal and hit enter.
5. open main.py
6. configure the input directory path at the top of the file. The input directory should contain one video, along with all of the hdf5 files produced by tierpsy. They can be organized however you wish within the directory, but they most all live somewhere inside your input directory.
7. run main.py using the green arrow button
8. find the outputs from ./output

And that's all! Let us know if you have any questions or additional needs related to the tool. 