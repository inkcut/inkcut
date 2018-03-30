### Device installation

#### Linux

##### Cutters with a parallel interface

Cutters with a parallel interface (either a 'real' parallel port or using a
built-in parallel-to-USB converter) must be added to your system as a printer
before using them from Inkcut. Start your printer configuration utility (e.g.
[system-config-printer](http://cyberelk.net/tim/software/system-config-printer)),
which at least when connecting via USB should detect the connected cutter.
Proceed to add it with the 'Generic' 'Raw Queue' driver.

### Device Setup

Choose `Device -> Setup...` from the menu. Select your device driver from the list. 

> Note: If your device is not in the list, use the `Inkcut Generic Driver`. 

Select the `Connection` tab and choose the connection type. Finally choose the language your device uses in the `Protocols` tab. Click `Ok` to save your changes.

![Inkcut - device setup](https://user-images.githubusercontent.com/380158/34272197-757a0ba0-e65d-11e7-9a12-d707bf0d68b9.gif)

### Speed settings

Inkcut attempts to send data to the device at a rate that will not cause the device's data buffer to overflow on large jobs. 
For this to work properly it is important that the speed setting matches the actual device speed.

### Output rotation

You can change final output scaling and rotation that Inkcut uses for your device under the `Output` tab within the `Device` tab.

![Inkcut - device final output](https://user-images.githubusercontent.com/380158/34272631-f86af5b4-e65e-11e7-82f0-1e3527f25213.gif)

### Add missing device

The list of supported devices from the old website was moved to a google spreadsheet [here](https://docs.google.com/spreadsheets/d/1KYNZMkNy0qYcpnXaNHgXKvdEhnUYKfGqZOH0Dw6siAg/). These must also be added into Inkcut
for them to display in the device dropdown list.

If you would like to add a missing device, please create an issue and provide the following:

- Manufacturer
- Model name
- Supported protocols
- Supported connection types
- Width and length of the plotting area
