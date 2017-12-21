
This section is meant to be a quickstart guide on using Inkcut. 

If you need help with something, first try searching the 
[issues list](https://github.com/codelv/inkcut/issues).


### Tutorial

Inkcut is now a stand alone application. You can either open an `svg` document
directly from Inkcut or from the Inkscape plugin.

### Opening from Inkscape

The Inkscape extension for Inkcut is under `Extensions -> Inkcut`. 
There are two options:

- `Cut selected...` will use only the currently selected paths (like the original version) 
- `Open document...` will use the whole document.

> Inkcut currently does not attempt to handle text nodes. Convert text to a path before
opening.

### Opening directly

Once installed, running the command `inkcut` will launch the application. Desktop
icons can also be used to launch it. Once launched use the `File -> Open...` menu
to open a document.


### Using inkcut

The basic workflow is the same. 

1. Open a document
2. Set the parameters
3. Start the job  

The new interface uses panels to separate similar options, such as weedlines or 
material size. These can be opened, closed, and move around however preferred.

### Starting a job

There are multiple ways to start a job:
 
 - Choose `Device -> Send to device` from the menu
 - Press `Start` from the the `Live` dock item
 - Right click and select `Send job to device` from the job history list
 
All of these will prompt for approval with a summary of the job before
starting. Pressing start will begin the process.

The status of the job can be monitored from the `Live` plot item which defaults
to a tab at the bottom of the screen. It displays a plot of the device movement path
with a progressbar to show how far along it is and options to pause or cancel midway
when supported by the device.




### Previous versions

This tutorial applies for Inkcut v1.0 and lower. 

##### Step 1

Select the paths you want to plot. All selection items must be of type path.

##### Step 2

Open Inkcut from Inkscape's extensions `menu -> Cutter/Plotter -> Inkcut v1.0`. 

![Inkcut extension](https://user-images.githubusercontent.com/380158/34217242-0da7bb88-e579-11e7-9f0a-3ba619be0648.jpeg)

Inkcut will open showing the general tab and the paths selected to plot in the preview.

![Inkcut general tab](https://user-images.githubusercontent.com/380158/34217513-b0a7a424-e579-11e7-955f-71860a7f6736.jpeg)

##### Step 3

Setup your device by clicking the device properties button. You only have to do this once and your settings will be saved the next time it's run.

![Inkcut device props](https://user-images.githubusercontent.com/380158/34217249-10882144-e579-11e7-88b8-aaf98b897eb5.jpeg)

##### Step 4

Click save then click on the options tab. A bunch of options can be adjusted from here, the most notable are the overcut, offset, and smoothness. Read the tooltips to understand what they do and use the preview button to see how it effects the output.

![Inkcut options](https://user-images.githubusercontent.com/380158/34217254-11dd1a54-e579-11e7-9553-9071ce982d7d.jpeg)

##### Step 5

When you're satisfied with the preview, click on the Plot Paths button to open the send data dialog. It will display some information about the plot as well as the data to be sent. Finally click send to send the data to your plotter.

![Inkcut cut dialog](https://user-images.githubusercontent.com/380158/34217257-139216f6-e579-11e7-8d79-eb3d422800d5.jpeg)

This is the result from this tutorial.

![Result](https://user-images.githubusercontent.com/380158/34217260-167718e4-e579-11e7-9cee-b158c3cf20eb.jpeg)


