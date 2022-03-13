import micropython
micropython.alloc_emergency_exception_buf(100)
import time
import random
import math
from machine import Pin




import machine, neopixel # brauch aktuelles pyboard, es geht mit 1.18

radar = Pin('X7', Pin.IN, Pin.PULL_DOWN)

taster = Pin('Y1', Pin.IN, Pin.PULL_UP)
taster_gnd = Pin('Y2', Pin.OUT)
taster_gnd.value(0)

automatisch_leuchte = False # ohne automatik leuchtet es erst auf knopfdruck

kette = 50
streifen = 5 * 96
#streifen = 2 * 144
leds =  streifen # kette+streifen
np = neopixel.NeoPixel(machine.Pin.board.Y12, leds, bpp=3, timing=1)
'''
for i in range(leds):
    np[i] = (255, 0, 0)
    np.write()
'''
np.fill((0,0,0))
np.write()


while False:
    peter=5
    np.fill((0,0,0))
    for i in range(200):
        np[i] = (0, 0, 255)
        np.write()
        time.sleep(1.0)
        np[i] = (0, 0, 80)
    print(time.time())


abdunkelphase = 500

# wave_array is an array with integers to max 255/2, colors
subschritte = 100
wave_array = [0] * subschritte
for i in range(subschritte):
    phase = i / subschritte * 2 * math.pi
    wave_array[i] = int( 0.5 * 255.0 * (-math.cos(phase) * 0.5 + 0.5)**2 )
#print (wave_array)

def zufallsding():
    global leds, subschritte
    colors=[
    (2,0,0), # red
    (2,1,0), # orange
    (2,2,0), # yellow
    (1,2,0), # giftgruen
    (0,2,0), # gruen
    (0,2,1), # grausiggruen
    (0,2,2), # cyan
    (0,1,2), # komischblau
    (0,0,2), # blau
    (1,0,2), # komischblau 2
    (2,0,2), # magenta
    (2,0,1), # komischpink
    (2,2,2) # weiss
    ]
    farbe = random.choice(colors)
    #increment_auswahl = [3,5,10,20,30,80]
    increment_auswahl = [5,10,20,30,80, 130, 200, 400, 500]
    increment = random.choice(increment_auswahl)  # beispiel: bei increment = subschritte: 1 led
    #[subschritte// 20]
    laenge = random.choice([50,30,20,10,5,2])
    length_wave_divider = subschritte//laenge
    position = -(subschritte//length_wave_divider)*subschritte
    #print(position)
    ding = {
        "farbe": farbe,
        "length_wave_divider": length_wave_divider,
        "increment": increment,
        "position": position,
        "lebensdauer": random.choice([3000, 4000, 5000, 7000, 15000]) + abdunkelphase,
        "blink": random.random() < 0.05
    }
    print('neues ding:', ding)
    return(ding)

dinger_liste = []
dinger_liste_fertige_fix = [
    {
        "farbe": (0,2,0), # gruen
        "length_wave_divider": subschritte//10,
        "increment": 3,
        "position": -10*subschritte,
        "lebensdauer": 1000,
        "blink": False
    },
    {
        "farbe": (0,0,2), # blau
        "length_wave_divider": subschritte//5,
        "increment": 13,
        "position": -5*subschritte,
        "lebensdauer": 1500,
        "blink": False
    },
    {
        "farbe": (2,0,0), # red
        "length_wave_divider": subschritte//3,
        "increment": 120,
        "position": -3*subschritte,
        "lebensdauer": 2000,
        "blink": False
    },
    {
        "farbe": (2,2,0), # yellow
        "length_wave_divider": subschritte//20,
        "increment": 70,
        "position": -20*subschritte,
        "lebensdauer": 2000,
        "blink": False
    },
    ]
dinger_liste_fertige = dinger_liste_fertige_fix

anzahl_dinger_max = 10 # vorsicht: stromverbrauch

idle_counter = 1000
counter = 0
counter_max = 100
ding_einfuegen = 0
blinki = False
def show_dinger():
    global leds, np, dinger_liste, subschritte, wave_array, counter, ding_einfuegen, blinki, idle_counter,dinger_liste_fertige ,dinger_liste_fertige_fix
    if len(dinger_liste) > 0:
        np.fill((0,0,0))
        for ding in dinger_liste:
            farbe = ding["farbe"]
            increment = ding["increment"]
            length_wave_divider = ding["length_wave_divider"]
            position = ding["position"]
            lebensdauer = ding["lebensdauer"]
            start_led =(position // subschritte) + 1
            stop_led = start_led + subschritte // length_wave_divider
            start_led = max(0, start_led) # nur positive anzeigen
            stop_led = min(leds, stop_led)
            for led in range(start_led, stop_led):
                #print('start_led % d, stop_led % s' % (start_led, stop_led))
                wave_array_pos = (led * subschritte - position ) // (subschritte //  length_wave_divider)  #led - start_led) * length_wave_divider
                #print('position % d start_led % d, wave_array_pos %d'%(position, start_led, wave_array_pos))
                if wave_array_pos < 0 or wave_array_pos > len(wave_array) -1 :
                    #print('wave_array_pos falsch %d' % wave_array_pos)
                    peter = 5
                else:
                    value = wave_array[wave_array_pos]
                    if lebensdauer < 0:
                        value = int(value +  float(lebensdauer)/float(abdunkelphase)*127.0)
                        value = max(0,value)
                    vorher = np.__getitem__(led)
                    farbe0 = min(value*farbe[0] + vorher[0], 255)
                    farbe1 = min(value*farbe[1] + vorher[1], 255)
                    farbe2 = min(value*farbe[2] + vorher[2], 255)
                    np.__setitem__(led,(farbe0, farbe1, farbe2))
                if ding["blink"] and blinki:
                    np.__setitem__(led,(0, 0, 0))
            ding["position"] = position + increment
            #print('position % d' % position)
            if position > leds * subschritte and increment > 0: # bounce at the end
                ding["increment"] = -increment
            if position < -subschritte * subschritte//length_wave_divider and increment < 0: # bounce at the start
                ding["increment"] = -increment
            #print('position %d' % position)
            ding["lebensdauer"] -= 1
            #print('alter %d' % alter)
        np.write()
        blinki = not blinki
    counter += 1
    if counter % counter_max == 0:
        #print('test auf alte')
        counter = 0
        neue_liste = []
        lebensdauern = []
        for ding in dinger_liste:
            if ding["lebensdauer"] > - abdunkelphase:
                neue_liste.append(ding)
                lebensdauern.append(ding["lebensdauer"])
            else:
                print('stirbt, es hat jetzt %d dinger' % (len(dinger_liste)-1))
        dinger_liste = neue_liste
        if len(lebensdauern) > 0:
            print('lebensdauer der %d dinger' % len(lebensdauern) ,  lebensdauern)
    if taster.value() == 0: # Taster gedrueckt
        #if len(dinger_liste) < anzahl_dinger_max: # limitiere die anzahl dinger
            ding_einfuegen = 3
    if ding_einfuegen > 0: # debounce
        ding_einfuegen -= 1
        if ding_einfuegen == 1:
            if len(dinger_liste_fertige) > 0:
                dinger_liste.append(dinger_liste_fertige.pop(0))
                #print('ding eingefuegt, es hat jetzt %d dinger' % len(dinger_liste))
            else:
                dinger_liste.append(zufallsding())
    if automatisch_leuchte:
        if random.random() < 0.0001:
            dinger_liste.append(zufallsding())
    zuviele_dinger = len(dinger_liste) - anzahl_dinger_max
    if zuviele_dinger > 0: # zu viele, aeltester sterben lassen
        for i in range(zuviele_dinger):
            if dinger_liste[i]["lebensdauer"] > 0:
                dinger_liste[i]["lebensdauer"] = 0
                print('reduziere lebensdauer da %d zuviele dinger' % zuviele_dinger)
        if zuviele_dinger > 4:
            del dinger_liste[0]
            print('geloescht da %d zuviele dinger' % zuviele_dinger)
    if len(dinger_liste) == 0:
        idle_counter += 1
        print ('idle_counter %d' % idle_counter)
        if idle_counter > 200:
            dinger_liste_fertige = dinger_liste_fertige_fix
        time.sleep(0.1)
    else:
        idle_counter = 0




while True:
    show_dinger()
    #time.sleep(1.0)
