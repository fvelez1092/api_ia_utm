from marshmallow import Schema, pre_load


class BaseSchema(Schema):
    @pre_load
    def string_to_none(self, data, **kwargs):
        def turn_to_none(x):
            return None if (x == "" or (x == 0 and isinstance(x, int))) else x

        if isinstance(data, list):
            for item in data:
                for k, v in item.items():
                    item[k] = turn_to_none(v)
        else:
            for k, v in data.items():
                data[k] = turn_to_none(v)

        return data
