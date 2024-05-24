import glob
import re
from argparse import ArgumentParser


def main():
    parser = ArgumentParser()
    parser.add_argument("--glob", default="../data/raw/*.txt")
    parser.add_argument("--save-dir", default="../data/chunked/")
    args = parser.parse_args()
    if not args.save_dir.endswith("/"):
        args.save_dir += "/"
    files = glob.glob(args.glob)
    for file in files:
        count = 0
        with open(file, "r") as f:
            lines = f.readlines()
        tmp_lines: list[str] = []
        for line in lines:
            l = replace_characters(line.strip())
            if not l:
                continue
            tmp_lines.append(l)
            count += len(l)
        divide_by = 1
        while True:
            if (count / divide_by) < 500:
                break
            divide_by += 1
        breakline_point = int(count / divide_by)
        tmp_save = ""
        tmp_last_line = ""
        save = ""
        chunk_length: list[int] = []
        for l in tmp_lines:
            tmp_save += l
            if len(tmp_save) >= breakline_point:
                save += f"{tmp_last_line}{tmp_save}\n"
                chunk_length.append(len(tmp_last_line) + len(tmp_save))
                tmp_save = ""
                tmp_last_line = l
        if tmp_save:
            save += f"{tmp_last_line}{tmp_save}\n"
            chunk_length.append(len(tmp_last_line) + len(tmp_save))
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
    s = re.sub("[１一]", "1", s)
    s = re.sub("[２二]", "2", s)
    s = re.sub("[３三]", "3", s)
    s = re.sub("[４四]", "4", s)
    s = re.sub("[５五]", "5", s)
    s = re.sub("[６六]", "6", s)
    s = re.sub("[７七]", "7", s)
    s = re.sub("[８八]", "8", s)
    s = re.sub("[９九]", "9", s)
    return s


if __name__ == "__main__":
    main()
