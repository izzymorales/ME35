import machine, asyncio, neopixel, izzy, mqtt
from machine import Pin, PWM
from mqtt import MQTTClient
nl = izzy.NightLight()

async def check_mqtt():
    def callback(topic, msg):
        global is_active
        if (msg.decode()) == 'start':
            is_active = True
            print('Activated!')
        elif (msg.decode()) == 'stop':
            is_active = False
            print('Off!')
        print((topic.decode(), msg.decode()))
    client = nl.mqtt_connect(callback)
    while True:
        client.check_msg()
        await asyncio.sleep(0.1)

async def check_btn():
    global is_active
    btn = Pin('GPIO20', Pin.IN)
    previous_btn_state = btn.value()
    while True: # change to MQTT statement
        global is_active
        if is_active:
            current_btn_state = btn.value()
            if previous_btn_state == False and current_btn_state == True: # Button was pressed and is now released
                print('button released!')
                nl.update_state(True) # Update state and NeoPixel light after release
                nl.beep(1000) # beep
            previous_btn_state = current_btn_state # Update the previous button state for the next loop
            await asyncio.sleep(0.01) # Small delay to avoid busy-waiting
        if not is_active:
            nl.reset()
            await asyncio.sleep(0.01)
    
async def breathe():
    global is_active
    while True:
        global is_active
        if is_active:
            await nl.led_breathe()
        if not is_active:
            nl.reset()
            await asyncio.sleep(0.01)
    
async def main():
    global is_active
    is_active = False
    nl.connect()
    tasks = asyncio.gather(check_mqtt(),check_btn(),breathe())
    await tasks # wait for duration
    
asyncio.run(main())
