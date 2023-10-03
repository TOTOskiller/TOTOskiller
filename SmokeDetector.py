import RPi.GPIO as GPIO
import array
import time
import smtplib
import statistics
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def send_email(smokeVal):
    i = 0

    email_user = "SenderEmail@gmail.com" #Anpassen
    email_password = "App-Passwort" #Anpassen
    email_send = ["Empfänger-Email"] #Anpassen

    subject = ("!!!Rauchmelder hat Rauch erkannt!!!")

    body = ("Unser Rauchmelder hat Rauch erkannt. \nDer Normalwert ohne Rauch liegt bei ungefähr 0.13, der Aktuelle beträgt %.2f" %smokeVal)

    for emails in email_send:
        msg = MIMEMultipart()
        msg["From"] = email_user
        msg["To"] = email_send[i]
        msg["Subject"] = subject
        msg.attach(MIMEText(body,"plain"))

        text = msg.as_string()
        server = smtplib.SMTP("smtp.gmail.com",587) #Anpassen wenn nich gmail als sender verwendet wird
        server.starttls()
        server.login(email_user,email_password)


        server.sendmail(email_user,email_send[i],text)
        server.quit()
        i = i + 1

# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8
mq2_dpin = 26 #Digital Output
mq2_apin = 0 # Analog Output?

#port init
def init():
         GPIO.setwarnings(False)
         GPIO.cleanup()			#clean up at the end of your script
         GPIO.setmode(GPIO.BCM)		#to specify whilch pin numbering system
         # set up the SPI interface pins
         GPIO.setup(SPIMOSI, GPIO.OUT)
         GPIO.setup(SPIMISO, GPIO.IN)
         GPIO.setup(SPICLK, GPIO.OUT)
         GPIO.setup(SPICS, GPIO.OUT)
         GPIO.setup(mq2_dpin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)

#read SPI data from MCP3008(or MCP3204, or MSP3208) chip,8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)	

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout
#main loop
def main():
         init()
         print("please wait...")
         time.sleep(20)
         i=0 #not necessary just for number of attempts
         n=0
         array_smokeVal = [0.12, 0.12, 0.12, 0.12, 0.12]
         while True:
                  if n == 5:
                      n = 0
                  i = i + 1
                  COlevel=readadc(mq2_apin, SPICLK, SPIMOSI, SPIMISO, SPICS)
                  smokeVal = ((COlevel/1024.)*3.3)
                  average_smokeVal = statistics.median(sorted(array_smokeVal))
                  
                  array_smokeVal[n] = float(smokeVal)
                  n = n + 1
                  
                  if average_smokeVal > 0.165:
                      print("Smoke is here: %.2f\n" %average_smokeVal)
                      send_email(average_smokeVal)
                      time.sleep(300)

                  else:
                      print("No smoke: %.2f\n" %average_smokeVal)
                      
                  time.sleep(0.1)
                    

if __name__ =='__main__':
         try:
                  main()
                  pass
         except KeyboardInterrupt:
                  pass

GPIO.cleanup() 
