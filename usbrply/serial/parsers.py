import binascii

FTDI_DEVICE_OUT_REQTYPE = 64
FTDI_DEVICE_IN_REQTYPE = 192

req_s2i = {
    "RESET": 0,
    "SET_MODEM_CTRL": 1,
    "SET_FLOW_CTRL": 2,
    "SET_BAUDRATE": 3,
    "SET_DATA": 4,
    "POLL_MODEM_STATUS": 0x05,
    "SET_EVENT_CHAR": 0x06,
    "SET_ERROR_CHAR": 0x07,
    "SET_LATENCY_TIMER": 0x09,
    "GET_LATENCY_TIMER": 0x0A,
    "SET_BITMODE": 0x0B,
    "READ_PINS": 0x0C,
    "READ_EEPROM": 0x90,
    "WRITE_EEPROM": 0x91,
    "ERASE_EEPROM": 0x92,
}
req_i2s = dict([(v, k) for k, v in req_s2i.items()])

INTERFACE_ANY = 0
INTERFACE_A = 1
INTERFACE_B = 2
INTERFACE_C = 3
INTERFACE_D = 4


def interface_i2str(i):
    if i == INTERFACE_A:
        return "A"
    elif i == INTERFACE_B:
        return "B"
    elif i == INTERFACE_C:
        return "C"
    elif i == INTERFACE_D:
        return "D"
    assert 0


def flags2dict(s2i, vali):
    ret = {}
    for k, v in s2i.items():
        ret[k] = bool(vali & v)
    return ret


# is a packet json output format but a serial input format
class FT2232CParser(object):
    def __init__(self, args):
        self.ascii = args.ascii
        self.jo = []

    def next_json(self, j, prefix=None):
        self.jo.append(j)

    def header(self):
        # comment("Generated by usbrply-serial FT2232C")
        pass

    def footer(self):
        pass

    def handleControlRead(self, d):
        print(d)
        if d['bRequestType'] != FTDI_DEVICE_IN_REQTYPE:
            return
        request = req_i2s[d['bRequest']]
        print("bRequest", request)
        if request == "POLL_MODEM_STATUS":
            assert d['wLength'] == 2
            buff = bytearray(binascii.unhexlify(d['data']))
            assert buff[1] & 0x0F == 0
            j = {
                # buff1
                # Clear to send
                'CTS': bool(buff[1] & 0x10),
                # Data set ready
                'DTS': bool(buff[1] & 0x20),
                # Ring indicator
                'RI': bool(buff[1] & 0x40),
                # Receive line signal detect
                'RLSD': bool(buff[1] & 0x80),
                # buff0
                # Data ready
                'DR': bool(buff[0] & 0x01),
                # Overrun error
                'OE': bool(buff[0] & 0x02),
                # Parity error
                'PE': bool(buff[0] & 0x04),
                # Framing error
                'FE': bool(buff[0] & 0x08),
                # Break interrupt
                'BI': bool(buff[0] & 0x10),
                # Transmitter holding register
                'THRE': bool(buff[0] & 0x20),
                # Transmitter empty
                'TEMT': bool(buff[0] & 0x40),
                # Error in RCVR FIFO
                'ERR': bool(buff[0] & 0x80),
            }
        else:
            j = {}
            j["type"] = request
            print("%s: FIXME" % (request, ))

        j["type"] = request
        j['rw'] = 'r'
        j['interface'] = interface_i2str(d["wIndex"] & 0xFF)
        self.next_json(j)

    def handleControlWrite(self, d):
        """
        ('bRequest', 'SET_EVENT_CHAR')
        SET_EVENT_CHAR: FIXME
        {'wValue': 0, 'data': '', 'bRequest': 7, 'packn': (301, 302), 'type': 'controlWrite', 'bRequestType': 64, 'wIndex': 1}
        ('bRequest', 'SET_ERROR_CHAR')
        SET_ERROR_CHAR: FIXME
        {'wValue': 1, 'data': '', 'bRequest': 9, 'packn': (303, 304), 'type': 'controlWrite', 'bRequestType': 64, 'wIndex': 1}
        ('bRequest', 'SET_LATENCY_TIMER')
        SET_LATENCY_TIMER: FIXME
        {'wValue': 0, 'data': '', 'bRequest': 2, 'packn': (305, 306), 'type': 'controlWrite', 'bRequestType': 64, 'wIndex': 257}
        ('bRequest', 'SET_FLOW_CTRL')
        {'wValue': 0, 'data': '', 'bRequest': 11, 'packn': (309, 310), 'type': 'controlWrite', 'bRequestType': 64, 'wIndex': 1}
        ('bRequest', 'SET_BITMODE')
        SET_BITMODE: FIXME
        {'wValue': 512, 'data': '', 'bRequest': 11, 'packn': (311, 312), 'type': 'controlWrite', 'bRequestType': 64, 'wIndex': 1}
        ('bRequest', 'SET_BITMODE')
        SET_BITMODE: FIXME
        {'wValue': 2, 'data': '', 'bRequest': 9, 'packn': (621, 622), 'type': 'controlWrite', 'bRequestType': 64, 'wIndex': 1}
        ('bRequest', 'SET_LATENCY_TIMER')
        SET_LATENCY_TIMER: FIXME
        """
        print(d)
        if d['bRequestType'] != FTDI_DEVICE_OUT_REQTYPE:
            return
        request = req_i2s[d['bRequest']]
        print("bRequest", request)

        def SET_FLOW_CTRL(d):
            flag_s2i = {
                "DISABLE_FLOW_CTRL": 0x0,
                "RTS_CTS_HS": 0x01,
                "DTR_DSR_HS": 0x02,
                "XON_XOFF_HS": 0x04,
            }
            return flags2dict(flag_s2i, d["wIndex"] >> 8)

        def SET_DATA(d):
            parity = {
                0: "NONE",
                1: "ODD",
                2: "EVEN",
                3: "MARK",
                4: "SPACE",
            }[(d['wValue'] >> 8) & 0x7]

            stopbits = {
                0: "1",
                1: "15",
                2: "2",
            }[(d['wValue'] >> 11) & 0x3]

            breakon = {
                0: "OFF",
                1: "ON",
            }[(d['wValue'] >> 14) & 0x1]

            j = {
                'parity': parity,
                'stopbits': stopbits,
                'breakon': breakon,
            }

            return j

        def SET_EVENT_CHAR(d):
            """Set the special event character"""
            j = {
                "char": d['wValue'] & 0xFF,
                "enable": bool(d['wValue'] & 0x100),
            }
            return j

        def SET_ERROR_CHAR(d):
            """Set error character"""
            j = {
                "char": d['wValue'] & 0xFF,
                "enable": bool(d['wValue'] & 0x100),
            }
            return j

        def SET_LATENCY_TIMER(d):
            """keeps data in the internal buffer if the buffer is not full yet"""
            latency = d['wValue']
            assert 1 <= latency <= 255
            j = {
                'latency': latency,
            }
            return j

        def SET_BITMODE(d):
            """
            FT_SetBitMode - mode = 0, mask = 0 - Reset the MPSSE controller. Perform a general reset on
            the MPSSE, not the port itself
            
            FT_SetBitMode - mode = 2, mask = 0 - Enable the MPSSE controller. Pin directions are set later
            through the MPSSE commands.
            """
            flag_s2i = {
                "RESET": 0x0,
                "BITBANG": 0x01,
                "MPSSE": 0x02,
                "SYNCBB": 0x04,
                "MCU": 0x08,
                "OPTO": 0x10,
                "CBUS": 0x20,
                "SYNCFF": 0x40,
                "FT1284": 0x80,
            }
            j = flags2dict(flag_s2i, d["wValue"] >> 8)
            j['bitmask'] = d["wValue"] & 0xFF
            return j

        def DEFAULT(d):
            j = {}
            print("%s: FIXME" % (request, ))
            return j

        j = {
            "SET_FLOW_CTRL": SET_FLOW_CTRL,
            "SET_DATA": SET_DATA,
            "SET_EVENT_CHAR": SET_EVENT_CHAR,
            "SET_ERROR_CHAR": SET_ERROR_CHAR,
            "SET_LATENCY_TIMER": SET_LATENCY_TIMER,
            "SET_BITMODE": SET_BITMODE,
        }.get(request, DEFAULT)(d)

        j["type"] = request
        j['rw'] = 'w'
        j['interface'] = interface_i2str(d["wIndex"] & 0xFF)
        self.next_json(j)

    def handleBulkWrite(self, d):
        # print(d)
        # json encodes in hex
        # protocol itself encodes in hex
        # data = binascii.unhexlify(d["data"])
        # print(len(data))

        interface = {
            0x02: 0,
            0x04: 1,
        }[d["endp"]]

        self.next_json({
            "type": "write",
            "interface": interface,
            "data": d["data"],
        })

    def handleBulkRead(self, d):
        assert len(d["data"]) % 2 == 0
        # json encodes in hex
        # protocol itself encodes in hex
        data = binascii.unhexlify(d["data"])
        # print(d)

        interface = {
            0x81: 0,
            0x83: 1,
        }[d["endp"]]

        prefix = data[0:2]
        data = data[2:]
        # meh lots of these and not sure what they mean
        # should look into these but just ignore for now
        # assert prefix == "\x42\x60" or prefix == "\x32\x60" or prefix == "\x32\x00", d

        if len(data):
            self.next_json({
                "type": "read",
                "interface": interface,
                "data": binascii.hexlify(data),
                "prefix": prefix,
            })

    def run(self, j):
        self.header()

        for di, d in enumerate(j["data"]):
            if 0 and di > 500:
                print("debug break")
                break
            if d["type"] == "bulkWrite":
                self.handleBulkWrite(d)
            elif d["type"] == "bulkRead":
                self.handleBulkRead(d)
            elif d["type"] == "controlRead":
                self.handleControlRead(d)
            elif d["type"] == "controlWrite":
                self.handleControlWrite(d)

        self.footer()
        j = {
            "data": self.jo,
        }
        return j
