Jairus Martin - 3/25/2011
===============================================================================
Inkcut Overview: Basic Application Goals and Interaction
===============================================================================
The ultimate goal is to make an SVG graphic be plotable by a vinyl cutter.  The
way that this is implemented is in terms of a Job and a Device. The job will
be an SVG graphic that has requirements (number of copies, size, cut order,
spacing, etc.).  The Device will be a literal device like a printer that has
phyical properties (width, length, etc.) and can interepret a graphic language
(HPGL,GPGL,DMPL,Camm). The application must take the requirements given by the
job and turn it into data that can be read by the device.  The application
must also be able to send the data to the physical device via a printer/serial
connection (or to a queue that is run separately from the application which
can later send the data). Keeping a history of jobs and materials is requested.

Job to Device Graphic Language
-------------------------------------------------------------------------------
I plan on implementing this in a two stage process. The first stage is a Job to
SVG converstion.  Since the input data is already an SVG and it is easy to
manipulate SVG's it makes sense to take the input SVG, copy it and then use the
requirements to make a new SVG that meets the requirements.

For example, if we had an input svg that had one star at the origin, and the
requirements were to make 10 copies with 5mm spacing, we would simply make a
new svg, clone the original star at 10 different positions that would give the
correct spacing.  The properties of the Device and Material used would need to
be taken into consideration for sizing and positioning purposes which would
still be straigforward.

Note: Although the Job will be created to be used on a specific device and
material, I still want it to be able to be independent of the device. As long
as the job is within the 'boundaries' of another device it can still be used
for this different device without having to be recreated.  The material will be
job specific (although easily changable).

Next, the second stage would be converting this SVG into the output graphic
language required by the Device.  This conversion would be independent of the
Job, thus any requirements specific to the device (blade offset, path overcut,
axis transformations, etc.) must be done in this stage.  I have not yet found
out the best way to do this, a script seems like the most appropriate at the
time.

Graphic Language to Physical Cutting/Plotting
-------------------------------------------------------------------------------


Keeping a history/logging
-------------------------------------------------------------------------------
