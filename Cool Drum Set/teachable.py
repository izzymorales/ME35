from pyscript.js_modules import teach, mqtt_library
import asyncio


class TM_manager:
    def __init__(self):
        self.model_url = "https://teachablemachine.withgoogle.com/models/uLnETrZKf/"
        self.num_classes = 3

        self.mqtt_topic = "ME35-24/boomtss"
        self.myClient = mqtt_library.myClient

    async def connect_mqtt(self):
        self.myClient.init()
        while not self.myClient.connected:
            await asyncio.sleep(0.1)

    async def run_model(self):
        s = teach.s
        s.URL2 = self.model_url
        await s.init()

    def send(self, msg):
        print('send ', msg)
        self.myClient.publish(self.mqtt_topic, str(msg))

    def get_predictions(self):
        predictions = []
        for i in range (self.num_classes):
            divElement = document.getElementById('class' + str(i))
            if divElement:
                divValue = divElement.innerHTML
                try:
                    label, value = divValue.split(': ')
                    predictions.append((label.strip(), float(value.strip())))
                except:
                    return ""
        return predictions

    async def run(self):
        threshold = 0.85
        last_sent_message = None
        while True:
            if self.myClient.connected:
                predictions = self.get_predictions()
                if predictions and len(predictions) == self.num_classes:
                    max_prediction = max(predictions, key=lambda x: x[1])
                    label, confidence = max_prediction

                    if confidence >= threshold:
                        if label == 'Loud' and last_sent_message != "3000":
                            self.send("3000")
                            last_sent_message = "3000"
                        elif label == "Quiet" and last_sent_message != "200":
                            self.send("200")
                            last_sent_message = "200"
                    else:
                        last_sent_message = None
            await asyncio.sleep(0.5)

tm_manger = TM_manager()
await tm_manger.connect_mqtt()
await tm_manger.run_model()
await tm_manger.run()
