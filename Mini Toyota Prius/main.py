from prius import CarLeft, CarRight

if True:
    import network
    import time

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('Tufts_Robot', '')

    print('Wi-Fi connection pending', end = '')
    while wlan.ifconfig()[0] == '0.0.0.0':
        print('.', end='')
        time.sleep(1)

    # We should have a valid IP now via DHCP
    print('\nWi-Fi connection successful: {}'.format(wlan.ifconfig()))
    
vroom = CarLeft()
#nwoom = CarRight()
