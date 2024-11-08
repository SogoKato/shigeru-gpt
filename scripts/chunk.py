import glob
import json
import re
from argparse import ArgumentParser

import tiktoken


def main():
    parser = ArgumentParser()
    parser.add_argument("--glob", default="../data/raw/*.txt")
    parser.add_argument("--save-dir", default="../data/chunked/")
    args = parser.parse_args()
    if not args.save_dir.endswith("/"):
        args.save_dir += "/"
    files = glob.glob(args.glob)
    encoding = tiktoken.get_encoding("cl100k_base")
    for file in files:
        count = 0
        metadata = []
        is_metadata_line = False
        with open(file, "r") as f:
            lines = f.readlines()
        tmp_lines: list[str] = []
        for line in lines:
            l = replace_characters(line.strip())
            if l == "---":
                is_metadata_line = not is_metadata_line
                continue
            if is_metadata_line:
                metadata.append(l)
                continue
            if not l:
                continue
            tmp_lines.append(l)
            count += len(encoding.encode(l))
        divide_by = 1
        while True:
            if (count / divide_by) < 2048:
                break
            divide_by += 1
        breakline_point = int(count / divide_by)
        tmp_save = ""
        tmp_last_line = ""
        save = "{}\n".format(metadata_lines_to_json(metadata))
        chunk_length: list[int] = []
        for l in tmp_lines:
            tmp_save += l
            if len(encoding.encode(tmp_save)) >= breakline_point:
                save += f"{tmp_last_line}{tmp_save}\n"
                chunk_length.append(
                    len(encoding.encode(tmp_last_line)) + len(encoding.encode(tmp_save))
                )
                tmp_save = ""
                tmp_last_line = l
        if tmp_save:
            save += f"{tmp_last_line}{tmp_save}\n"
            chunk_length.append(
                len(encoding.encode(tmp_last_line)) + len(encoding.encode(tmp_save))
            )
        if len(chunk_length) != divide_by:
            print("WARNING: chunks does not match with division.")
        filename = file.split("/")[-1]
        savepath = f"{args.save_dir}{filename}"
        with open(savepath, "w") as f:
            f.write(save)
        print(
            f"{savepath} has been saved. {count}/{divide_by}={breakline_point}. chunk length: {chunk_length}"
        )


def replace_characters(s: str) -> str:
    s = re.sub("T\\d{2}:\\d{2}:\\d{2}\+\\d{2}:\\d{2}", "", s)
    s = re.sub("[　・、,]", "", s)
    s = re.sub("！", "!", s)
    s = re.sub("？", "?", s)
    s = re.sub("０", "0", s)
    s = re.sub("１", "1", s)
    s = re.sub("２", "2", s)
    s = re.sub("３", "3", s)
    s = re.sub("４", "4", s)
    s = re.sub("５", "5", s)
    s = re.sub("６", "6", s)
    s = re.sub("７", "7", s)
    s = re.sub("８", "8", s)
    s = re.sub("９", "9", s)
    return s


def metadata_lines_to_json(metadata: list[str]) -> str:
    d = {}
    for item in metadata:
        kv = item.split(": ")
        d[kv[0]] = kv[1]
    return json.dumps(d, ensure_ascii=False)


if __name__ == "__main__":
    main()
