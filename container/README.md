# Inkcut via container image;
Install inkcut to your linux OS by running the `distrobox-assemble create` command below.  
The python environment is already built-out, inkcut is ready-to-run.  

This approach is distribution agnostic, and is ideal for use on immutable OS's.  

## distrobox-assemble create
The paths and flags and apps-to-export are declared in a `distrobox.ini` file;  
simply point the distrobox-assemble command to this file.

```sh
distrobox-assemble create \
--name inkcutEnv \
--file https://raw.githubusercontent.com/inkcut/inkcut/refs/heads/master/container/distrobox.ini
```

[distrobox.ini contents:](distrobox.ini)  
```ini
[inkcutEnv]
name=inkcutEnv
image=ghcr.io/inkcut/inkcut:latest
home=$HOME/.local/share/distrobox/inkcutEnv
additional_flags="--group-add keep-groups"
exported_apps=/opt/inkcut-env/share/applications/inkcut.desktop
exported_bins=/opt/inkcut-env/bin/inkcut
exported_bins_path="$HOME/.local/bin"
pull=true
replace=true
```

# Error: 'Permission denied: /dev/tty...'
When using serial interfaces, this is a common (& expected) error.  
There are special permissions required to allow inkcut to access the hardware.

## Safe-enough, easiest:
Add 'yourusername' to the `dialout` group.  

This provides the user with access to more devices than is really needed, but is not likely a problem if you are the primary & sole user of the system.
```sh
sudo usermod -aG dialout yourusername
#logout & back in for group permissions to take effect
```

## More targeted approach:
Device access via udev rule

### Create udev rule for one specific device, and limit access to one user.
common path & filename: `/etc/udev/rules.d/50-usb-serial.rules`  

example contents:
This means using the vendor ID and product ID in the UDEV rule.  
```yml
# Match specific USB serial device by vendor and product ID
SUBSYSTEM=="tty", ATTRS{idVendor}=="067b", ATTRS{idProduct}=="2303", GROUP="yourusername", MODE="0660"
```

### Grant privilege to a range of devices, but limit access to one user
```yml
KERNEL=="ttyACM[0-9]*", SUBSYSTEMS=="usb", GROUP="yourusername", MODE:="0660", ENV{ID_MM_DEVICE_IGNORE}="1", ENV{ID_MM_PORT_IGNORE}="1"
# or for some usb-serial interfaces:
KERNEL=="ttyUSB[0-9]*", SUBSYSTEMS=="usb", GROUP="yourusername", MODE:="0660", ENV{ID_MM_DEVICE_IGNORE}="1", ENV{ID_MM_PORT_IGNORE}="1"
```

### Once you have chosen your udev approach:
```sh
[cyril@bluefin ~]$ sudo udevadm control --reload-rules
[cyril@bluefin ~]$ sudo udevadm trigger
```

after running one of the above udev rules, we can see that we have permissions from inside the container:
```sh
[cyril@bluefin ~]$ ls -l /dev/ttyA*
crw-rw---- 1 root cyril 166, 0 Jun 26 08:09 /dev/ttyACM0
[cyril@bluefin ~]$ distrobox enter inkcutEnv
📦[cyril@inkcutEnv cyril]$ ls -l /dev/ttyA*
crw-rw---- 1 nobody cyril 166, 0 Jun 26 08:09 /dev/ttyACM0
📦[cyril@inkcutEnv cyril]$
```
