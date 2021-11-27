from machine import ADC, Pin

adc = ADC(Pin(32))          # create ADC object on ADC pin

adc.atten(ADC.ATTN_11DB)    # set 11dB input attenuation (voltage range roughly 0.0v - 3.6v)
adc.width(ADC.WIDTH_12BIT)   # set 9 bit return values (returned range 0-511)
a = adc.read()
print(a)