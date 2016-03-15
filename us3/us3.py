#!/usr/bin/python
# -*- coding: utf-8 -*-

r"""
           _____
 _   _ ___|___ / 
| | | / __| |_ \ 
| |_| \__ \___) |
 \__,_|___/____/ 

us3 helps you to manage files on AWS S3 or S3 compatible API.
Usefull with Continuous Integreation pipelines :)

Author: Ahmet Demir <me@ahmet2mir.eu>
Sources: https://github.com/ahmet2mir/us3.git

Usage:
    us3 (upload|download) [options] -s <src>
    us3 delete [options] -s <src>

Options:
    -h --help                                   Show this screen.
    --version                                   Show version.

    -a <access> --access=<access>               Access key.
    -x <secret> --secret=<secret>               Secret key.
    -e <endpoint> --endpoint=<endpoint>         Host to connect to. Default 
                                                is s3.amazonaws.com.
    -i <is_secure> --is_secure=<is_secure>      Use secure connection (https) 
                                                or not (http). Default is True.
    -k <clg> --calling_format=<clg>             Choose how to call the S3 API. 
                                                Allowed:
                                                - SubdomainCallingFormat (default)
                                                - VHostCallingFormat
                                                - OrdinaryCallingFormat 
                                                - ProtocolIndependentOrdinaryCallingFormat.
    -b <bucket> --bucket=<bucket>               Bucket name.
    -s <src> --source=<src>                     File to download/upload.
    -d <dest> --destination=<dest>              Destination folder.
    -c <config.yml> --config=<config.yml>       Config file.

"""
from __future__ import absolute_import, print_function

import os
import sys
import math
import time
import logging

# third
import yaml
from docopt import docopt

# boto
import boto
from boto import exception
from boto.s3.key import Key
import boto.s3.connection
from filechunkio import FileChunkIO

CALLING_FORMATS = {
    'SubdomainCallingFormat': boto.s3.connection.SubdomainCallingFormat,
    'VHostCallingFormat': boto.s3.connection.VHostCallingFormat,
    'OrdinaryCallingFormat': boto.s3.connection.OrdinaryCallingFormat,
    'ProtocolIndependentOrdinaryCallingFormat':
        boto.s3.connection.ProtocolIndependentOrdinaryCallingFormat
}

# Manage colors
class bcolors:
    RED = '\033[1m\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    ENDC = '\033[0m'


def update_progress(progress, speed, elapsed):
    """ Progress bar http://stackoverflow.com/a/15860757"""
    barLength = 10 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "in {0}s".format(elapsed)
    block = int(round(barLength*progress))
    
    if speed > 1073741824:
        speed_v = speed / 1073741824
        speed_s = "GiB"
    elif speed > 1048576:
        speed_v = speed / 1048576
        speed_s = "MiB"
    elif speed > 1024:
        speed_v = speed / 1024
        speed_s = "KiB"
    else:
        speed_v = speed
        speed_s = "B"

    text = "\rPercent: [{0}] {1}% {2} -> {3} {4}/s".format( "#"*block + "-"*(barLength-block), int(progress*100), status, speed_v, speed_s)
    sys.stdout.write(bcolors.YELLOW + text + bcolors.ENDC)
    sys.stdout.flush()


def str2bool(value):
    """
    Convert string or int True or False

    :param value: value to convert
    :type value: str

    :return: True if value in ("yes", "true", "t", "1")
    :rtype: bool
    """
    return str(value).lower() in ("yes", "true", "t", "1")


def config(arguments):
    """ Manage configuration """
    data = {}
    conf_keys = ["access", "secret", "endpoint", "is_secure",
                 "calling_format", "source", "destination",
                 "bucket"]
    mandatory = ["access", "secret", "source", "bucket"]

    # default values
    data["is_secure"] = True
    data["calling_format"] = "SubdomainCallingFormat"
    data["endpoint"] = "s3.amazonaws.com"
    data["destination"] = None

    # Conf from config file or default config file
    if "--config" in arguments and arguments["--config"]:
        with open(arguments["--config"], 'r') as fb:
            data = yaml.safe_load(fb)
    elif os.environ.get("US3_CONFIG", None):
        with open(os.environ["US3_CONFIG"], 'r') as fb:
            data = yaml.safe_load(fb)
    elif os.path.isfile("/etc/default/us3.yaml"):
        with open("/etc/default/us3.yaml", 'r') as fb:
            data = yaml.safe_load(fb)

    # erase
    for conf_key in conf_keys:
        key_arg = "--{0}".format(conf_key)
        key_data = "US3_{0}".format(conf_key).upper()

        # vars from cli
        if arguments.get(key_arg, None):
            data[conf_key] = arguments[key_arg]

        # env variables, override YAML config
        if os.environ.get(key_data, None):
            data[conf_key] = os.environ[key_data]

        # Check
        if conf_key in mandatory and not data.get(conf_key):
            error = "Variable '{0}' is not setted or empty."
            print(bcolors.RED + error.format(conf_key) + bcolors.ENDC)
            sys.exit(2)
    return data


def get_bucket(config, name):
    """ Retrieve bucket object """
    try:
        conn = boto.connect_s3(
            aws_access_key_id = config["access"],
            aws_secret_access_key = config["secret"],
            host = config["endpoint"],
            is_secure = str2bool(config["is_secure"]),
            calling_format = CALLING_FORMATS[config["calling_format"]]()
        )
        return conn.get_bucket(name)
    except BaseException, e:
        print(bcolors.RED + str(e) + bcolors.ENDC)
        sys.exit(1)


def upload(bucket, source_file, dest_folder=None):
    """ http://boto.readthedocs.org/en/latest/s3_tut.html """
    # Get file info
    source_size = os.stat(source_file).st_size
    # Create a multipart upload request
    dest_path = os.path.basename(source_file)
    if dest_folder:
        if not dest_folder.endswith("/"):
            dest_folder += "/"
        dest_path = dest_folder + dest_path

    mp = bucket.initiate_multipart_upload(dest_path)
    start_time = time.mktime(time.localtime())

    # Use a chunk size of 8 MiB (feel free to change this)
    chunk_size = 8388608
    chunk_count = int(math.ceil(source_size / float(chunk_size)))
    speed = 0
    # Send the file parts, using FileChunkIO to create a file-like object
    # that points to a certain byte range within the original file. We
    # set bytes to never exceed the original file size.
    for i in range(chunk_count):
        offset = chunk_size * i
        bytes = min(chunk_size, source_size - offset)
        with FileChunkIO(source_file, 'r', offset=offset, bytes=bytes) as fp:
            mp.upload_part_from_file(fp, part_num=i + 1)
            end_time = time.mktime(time.localtime())
            if i > 1:
                speed = int(offset / (end_time - start_time))
            update_progress(i/float(chunk_count), speed, (end_time - start_time))

    # Finish the upload
    mp.complete_upload()
    update_progress(chunk_count/float(chunk_count), speed, (end_time - start_time))


def download(bucket, filename, output):
    k = Key(bucket)
    k.key = filename.strip()
    try:
        k.get_contents_to_filename(output)
        return True
    except BaseException, e:
        print(bcolors.RED + str(e) + bcolors.ENDC)
        sys.exit(3)


def delete(bucket, filename):
    k = Key(bucket)
    k.key = filename
    try:
        k.delete()
        return True
    except BaseException, e:
        print(bcolors.RED + str(e) + bcolors.ENDC)
        sys.exit(4)


def main():
    arguments = docopt(__doc__, version='US3 CLI 0.1')
    # init
    print(bcolors.GREEN + "===> Init S3 connection and retrieve bucket" + bcolors.ENDC)
    c = config(arguments)
    bucket = get_bucket(c, c["bucket"])

    if "upload" in arguments and arguments["upload"]:
        print(bcolors.GREEN + "===> Uploading %s" % c["source"] + bcolors.ENDC)
        upload(bucket, c["source"], c["destination"])
        print(bcolors.GREEN + "===> Done." + bcolors.ENDC)

    elif "download" in arguments and arguments["download"]:
        print(bcolors.GREEN + "===> Downloading %s" % c["source"] + bcolors.ENDC)
        # original filename
        output = os.path.basename(c["source"])
        if c["destination"]:
            output = c["destination"].rstrip("/") + "/" + os.path.basename(c["source"])
        download(bucket, c["source"], output)
        print(bcolors.GREEN + "===> Done." + bcolors.ENDC)

    elif "delete" in arguments and arguments["delete"]:
        print(bcolors.GREEN + "===> Deleting %s" % c["source"] + bcolors.ENDC)
        # original filename
        output = os.path.basename(c["source"])
        delete(bucket, c["source"])
        print(bcolors.GREEN + "===> Done." + bcolors.ENDC)

    else:
        print(__doc__)


if __name__ == '__main__':
    main()
