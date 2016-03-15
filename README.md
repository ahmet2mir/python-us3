
               _____ 
     _   _ ___|___ / 
    | | | / __| |_ \ 
    | |_| \__ \___) |
     \__,_|___/____/ 

us3 helps you to manage files on AWS S3 or S3 compatible API like Ceph or Cleversafe. Usefull with Continuous Integreation pipelines :)

## Installation

    pip install us3

For Docker check bottom

## Usage

    us3 (upload|download) [options] -s <src>
    us3 delete [options] -s <src>

## Options

    -h --help                                   Show this screen.
    --version                                   Show version.
    -a <access> --access=<access>               Access key.
    -x <secret> --secret=<secret>               Secret key.
    -e <endpoint> --endpoint=<endpoint>         Host to connect to. Default 
                                                is s3.amazonaws.com. You can [check all AWS host/region](http://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region)
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
    -d <dest> --destination=<dest>               Destination folder path.
    -c <config.yml> --config=<config.yml>       Config file path.

**Thoses values are overrided by environment variables.**


### Config file

You could use a config file in `YAML` format to reduce options in CLI.

By default, `us3` will look at `/etc/default/us3.yaml` or to the custom path with `--config <pathtoconf>`.

**Thoses values are overrided by the CLI and environment variables.**

Example:

    $ cat /etc/default/us3.yaml
    ---
    host:  mycustomhost
    access: myaccesskey
    secret: mysecurekey
    calling_format: OrdinaryCallingFormat
    is_secure: False

### Environment variables

Environment variables **had priority** on config values and CLI values. To export a value, prepend variable name uppered with `US3_`.

Example:

    export US3_HOST= myexporthost
    export US3_ACCESS=myaccesskey
    export US3_SECRET=mysecurekey

## Docker

Image size ~70MB

    docker pull ahmet2mir/us3

And use environment variables. By default, files are stored in /data

    docker run --rm \
        -e "US3_ENDPOINT=s3-eu-west-1.amazonaws.com" \
        -e 'US3_BUCKET=xxxx' \
        -e 'US3_ACCESS=yyyy' \
        -e 'US3_SECRET=zzzz+' \
        -v /tmp/docker:/data \
        ahmet2mir/us3 download -s myfile

## Licence

Apache License Version 2.0, January 2004