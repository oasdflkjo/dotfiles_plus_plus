currently just a task bar toggler with win+f12

in future some automatic window management will be added if i get around to it

so a bit progress but not much this is quite brute force

but atleas proof of concept works this way

so when prgram starts we intercept the event and then resize the window


not sure yet how to make this a real manager

should be as automatic as possible

and when new windows get introduced it should be really simple to add and do pixel perfect tweaking

im not after tiling window managers like i3

i prefer to have clean "dashboard" like environment with as little as possible of clutter

and when we expand this we would have shortcuts to different apps

also there is possibility to skip shortcuts and do just writing

win key is a good candidate for this 

if i want to open chrome i do win and type ch<tab> enter and chrome opens

that is quite simple 


TODO:

1.
psutil.Process(pid).name() use this to identify windows...

2.
{
  "Chrome": {"x": 100, "y": 100, "width": 800, "height": 600},
  ...
}

3. 
automatically detect new windows and add them to the json

4.
for general use needs a way to handle windows zoom level...
now windows reports actaul screen size / 1.25...


so game plan prolly is to make a software that catches all the windows and makes a datastructure of them

then tranform that datastructure into a json with current postition values

then our resizer layer just reads that json does resizing

and finally our window manager app applys the json valuew to windows

this will be quite clean and they have common datastructure that can be the interface

there should be some kind of designer more that allows to make layouts and json could choose predefined positions

goal is to do this only with python and minimal dependencies but still efficient enough









