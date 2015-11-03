
import types
from . import utils

class Entity(object):
    transform_attributes = {}

    def __init__(self, API, obj_dict):
        self.API = API
        self._init_from_detail_dict(obj_dict)


    def _init_from_detail_dict(self, obj_dict):
        self._init_attributes(obj_dict)


    def _init_attributes(self, obj_dict):
        for key, val in obj_dict.items():
            # Optionally convert values using the given transform functions
            # for the specific object type
            trans = self.transform_attributes.get(key)
            if trans:
                add_api_obj, trans_func = trans
                if add_api_obj:
                    val = trans_func(self.API, val)
                else:
                    val = trans_func(val)

            # Transform keys from camel case to our style
            key = utils.decamel(key)

            setattr(self, key, val)


class Channel(Entity):
    @classmethod
    def from_channel_dicts(self, API, channel_dicts):
        channels = []
        for channel_dict in channel_dicts:
            channels.append(Channel(API, channel_dict))
        return channels


    def get_value(self):
        if self.is_readable:
            return self.API.Channel_getValue(id=self.id)



class Device(Entity):
    transform_attributes = {
        "id"               : (False, int),
        "deviceId"         : (False, int),
        "operateGroupOnly" : (False, lambda v: v != "false"),
        "channels"         : (True,  Channel.from_channel_dicts),
    }

    @classmethod
    def get_devices(self, API, device_type=None):
        devices = API.Device_listAllDetail()

        if type(device_type) in [str, unicode]:
            device_type = [device_type]

        device_objects = []
        for device_dict in devices:
            if device_type == None or device_dict["type"] in device_type:
                device_class = device_classes_by_type_name.get(device_dict["type"], Device)
                device_objects.append(device_class(API, device_dict))
        return device_objects


    def get_values(self):
        values = []
        for channel in self.channels:
            values.append(channel.get_value())
        return values


    def formated_value(self):
        return repr(self.get_values())


class SpecificDevice(Device):
    @classmethod
    def get_all(self, API):
        return Device.get_devices(API, device_type=self.type_name)


class HMSecSC(SpecificDevice):
    type_name = "HM-Sec-SC"


    def is_open(self):
        return self.get_values()[0] != "false"


    def formated_value(self):
        return self.is_open() and "open" or "closed"


# Build a list of all specific product classes. If a device is initialized
# Device() checks whether or not a specific class or the generic Device()
# class should be used to initialize an object.
device_classes_by_type_name = {}
for key, val in globals().items():
    if isinstance(val, (type, types.ClassType)):
        if issubclass(val, Device) and key not in [ "Device", "SpecificDevice" ]:
                device_classes_by_type_name[val.type_name] = val
