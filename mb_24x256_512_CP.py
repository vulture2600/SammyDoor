# import bitbangio
# import busio
# from board import *
# import digitalio
# import time


# class mb_24x256_512_CP:
# 	def __init__(self, i2c, i2c_address, EEPROM_device):
# 		self.i2c = i2c
# 		self.i2c_address = i2c_address[0]


# 		if (EEPROM_device == "24x256"):
# 			self._MAX_ADDRESS = 32767
# 		elif (EEPROM_device == "24x512"):
# 			self._MAX_ADDRESS = 65535
# 		else:
# 			raise ValueError("Please choose a dev from the list")
# 			return()
# 		self.address_byte = [0,0]
# 	#init finished

# 	def write_byte (self, address, data):
# 		if((address > self._MAX_ADDRESS) or (address < 0)):
# 			raise ValueError("Address is outside of dev address range")
# 			return()

# 		if ((data > 255) or (data < 0)):
# 			raise ValueError ("you can only pass an 8-bit value 0-255 to this function")
# 			return()

# 		self.address_byte[1] = address & 0x00ff
# 		print(self.address_byte[1])
# 		self.address_byte[0] = address >> 8
# 		print(self.address_byte[0])

# 		# print(str(bytes([self.address_byte[0], self.address_byte[1]], data)))


# 		self.i2c.writeto(self.i2c_address, bytes([self.address_byte[0], self.address_byte[1], data]))
# 		time.sleep(.01) 
# 		#eeprom slow, needs time

# 	def read_byte(self, address):
# 		if((address > self._MAX_ADDRESS) or (address < 0)):
# 			raise ValueError("Address is out of range")
# 			return()


# 		self.address_byte[1] = address & 0x00ff
# 		self.address_byte[0] = address >> 8
# 		self.value_read = bytearray(1)
# 		self.i2c.writeto_then_readfrom(self.i2c_address, bytes([self.address_byte[0], (self.address_byte[1])]), self.value_read)
# 		self.value_read = int.from_bytes(self.value_read, 'big')
# 		return(self.value_read) 


#pasted:
import bitbangio
import busio
from board import *
import digitalio
import time


class mb_24x256_512_CP:
    """Driver for Microchip 24x256/512 EEPROM devices"""

    def __init__(self, i2c, i2c_address, EEPROM_device):
        # Init with the I2C setting
        self.i2c = i2c
        self.i2c_address = i2c_address[0]

        if(EEPROM_device == "24x256"):
            self._MAX_ADDRESS = 32767
        elif(EEPROM_device == "24x512"):
            self._MAX_ADDRESS = 65535
        else:
            raise ValueError("Please choose a device from the list")

            return()
        self.address_byte=[0,0]

    # Done init, ready to go

    def write_byte(self, address, data):
        if((address > self._MAX_ADDRESS) or (address < 0)):
            raise ValueError("Address is outside of device address range")
            return()

        if((data > 255) or (data < 0)):
            raise ValueError("You can only pass an 8-bit data value 0-255 to this function")
            return()

        self.address_byte[1] = address & 0x00ff
        self.address_byte[0] = address >> 8

        self.i2c.writeto(self.i2c_address, bytes([self.address_byte[0],self.address_byte[1], data]))
        time.sleep(0.01) # EEPROM needs time to write and will not respond if not ready


    def read_byte(self, address):
        if((address > self._MAX_ADDRESS) or (address < 0)):
            raise ValueError("Address is outside of device address range")
            return()

        self.address_byte[1] = address & 0x00ff
        self.address_byte[0] = address >> 8
        self.value_read = bytearray(1)
        self.i2c.writeto_then_readfrom(self.i2c_address, bytes([self.address_byte[0], (self.address_byte[1])]), self.value_read)
        self.value_read = int.from_bytes(self.value_read, "big")
        return(self.value_read)
