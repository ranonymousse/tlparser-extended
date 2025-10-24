import json
import pprint


class Configuration:

    def __init__(
        self,
        file_data_in="",
        folder_data_out="",
        only_with_status=None,
        logic_order=None,
        color_palette=None,
    ):
        self.file_data_in = file_data_in
        self.folder_data_out = folder_data_out
        self.only_with_status = only_with_status if only_with_status is not None else []
        self.logic_order = logic_order if logic_order is not None else []
        self.color_palette = color_palette if color_palette is not None else {}

    @classmethod
    def from_json(cls, file_path):
        with open(file_path, "r") as file:
            data = json.load(file)
        file_data_in = data.get("file_data_in", "")
        folder_data_out = data.get("folder_data_out", "")
        only_with_status = data.get("only_with_status", [])
        return cls(file_data_in, folder_data_out, only_with_status)

    def __str__(self):
        return pprint.pformat(self.__dict__, indent=2)
