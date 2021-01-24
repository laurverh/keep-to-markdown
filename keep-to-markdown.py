#!/usr/bin/env python3

import os
import sys
import glob
import json
from datetime import datetime as dt
from shutil import copy2 as cp
import mimetypes

output_path = "../markdown-notes"
unsupported_information = [
    "color",
    "isTrashed",
    "isPinned",
    "isArchived",
    "sharees",
]


def copy_file(file, path):
    try:
        cp(f"{path}{file}", f"{output_path}/resource/")
    except FileNotFoundError:
        # print(f'ERROR: File "{file}" not found in {path}')
        return False
    else:
        return True


def read_annotations(list) -> str:
    annotations_list = "*Weblinks:*"
    for entry in list:
        if entry["source"] == "WEBLINK":
            title = entry["title"]
            url = entry["url"]
            annotations_list += f" [{title}]({url});"
    return annotations_list


def read_attachments(list, path) -> str:
    attachments_list = "*Attachments:*\n"
    for entry in list:
        if "image" in entry["mimetype"]:
            image = entry["filePath"]
            if copy_file(image, path) is False:
                image_was_copied = False
                # Falls die Datei nicht gefunden werden konnte,
                # wird geprüft ob es die Datei unter einem
                # anderen Dateiformat zufinden ist.
                # Google benutzt '.jpeg' statt '.jpg' -- doof
                image_type = mimetypes.guess_type(f"{path}{image}")
                types = mimetypes.guess_all_extensions(image_type[0])
                for type in types:
                    if type in image:
                        image_name = image.replace(type, "")
                        for t in types:
                            if len(glob.glob(f"{path}{image_name}{t}")) > 0:
                                image = f"{image_name}{t}"
                                # print(f'Found "{image}"')
                                copy_file(image, path)
                                if copy_file(image, path) is True:
                                    image_was_copied = True
                if not image_was_copied:
                    print(f'ERROR: Image "{image}" not found in {path}')
            attachments_list += f"![{image}](resource/{image})\n"
    return attachments_list


def read_tasklist(list) -> str:
    content_list = "*Tasklist:*\n"
    for entry in list:
        text = entry["text"]
        if entry["isChecked"] is True:
            content_list += f"- [x] {text}\n"
        else:
            content_list += f"- [ ] {text}\n"
    return content_list


def read_tags(tags) -> str:
    tag_list = "tags:"
    for entry in tags:
        tag = entry["name"]
        tag_list += f" {tag};"
    return tag_list


def read_write_notes(path):
    notes = glob.glob(f"{path}/*.json")
    for note in notes:
        with open(note, "r") as jsonfile:
            data = json.load(jsonfile)

            timestamp = data.pop("userEditedTimestampUsec")
            if timestamp == 0:
                iso_datetime = dt.now().strftime("%Y-%m-%d %H:%M:%S edited")
            else:
                iso_datetime = dt.fromtimestamp(timestamp / 1000000).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            title = data.pop("title")
            if title != "":
                title = str(title).replace("/", "_")
                if len(title) > 100:
                    title = title[0:99]
            else:
                title = "No Title"

            title += f" {iso_datetime}"

            if not os.path.exists(f"{output_path}/{title}.md"):
                # print(f"Convert: {title}")
                with open(f"{output_path}/{title}.md", "w") as mdfile:
                    mdfile.write(f"---\n")
                    mdfile.write(f"title: {title}\n")
                    if title != iso_datetime:
                        mdfile.write(f"date: {iso_datetime}\n")
                    # add tags
                    try:
                        tags = read_tags(data.pop("labels"))
                        # tags = read_tags(data["labels"])
                        # del data["labels"]
                        # print(f"Tags: {tags}")
                        mdfile.write(f"{tags}\n")
                    except KeyError:
                        pass
                        # print("No tags available.")
                    mdfile.write(f"---\n\n")
                    # add text content
                    try:
                        textContent = data.pop("textContent")
                        mdfile.write(f"{textContent}\n\n")
                    except KeyError:
                        pass
                        # print("No text content available.")
                    # add tasklist
                    try:
                        tasklist = read_tasklist(data.pop("listContent"))
                        mdfile.write(f"{tasklist}\n\n")
                    except KeyError:
                        pass
                        # print("No tasklist available.")
                    # add annotations
                    try:
                        annotations = read_annotations(data.pop("annotations"))
                        mdfile.write(f"{annotations}")
                    except KeyError:
                        pass
                        # print("No annotations available.")
                    # add attachments
                    try:
                        attachments = read_attachments(data.pop("attachments"), path)
                        mdfile.write(f"{attachments}")
                    except KeyError:
                        pass
                        # print("No attachments available.")
            else:
                pass
                # print(f'ERROR: File "{title}" exists!')

            keys = set(data.keys())
            for item in unsupported_information:
                try:
                    keys.remove(item)
                except KeyError:
                    pass
            if keys:
                print(
                    f"ERROR: Not all data from {note} could be parsed. These keys remain:\n{keys} "
                )


def create_folder():
    try:
        os.makedirs(f"{output_path}/resource")
        # print('Create folder "notes" - home of markdown files.')
    except OSError:
        print("ERROR: Creation of folders failed.")


if __name__ == "__main__":
    create_folder()
    try:
        read_write_notes(sys.argv[1])
    except IndexError:
        print("ERROR: Please enter a correct path!")
