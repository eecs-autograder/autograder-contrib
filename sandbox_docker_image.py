#! /usr/bin/env python3

import argparse
import os
from typing import Optional
from urllib.parse import urljoin

import requests

from ag_contrib import http_client, utils


def main():
    args = parse_args()

    client = None
    try:
        client = http_client.HTTPClient.make_default(
            args.token_file, args.base_url)
    except utils.TokenFileNotFound as e:
        print(e)
        exit(1)

    if args.command == 'list':
        list_images(client)
    elif args.command == 'detail':
        image_detail(client, args.pk)
    elif args.command == 'create':
        create_image(client,
                     args.name, args.display_name, args.tag)
    elif args.command == 'edit':
        edit_image(client, args.pk, args.display_name, args.tag)


def list_images(client: http_client.HTTPClient):
    response = client.get('/api/sandbox_docker_images/')
    http_client.check_response_status(response)

    for image in response.json():
        print(image_to_str(image))


def image_detail(client: http_client.HTTPClient, pk: int):
    response = client.get(f'/api/sandbox_docker_images/{pk}/')
    http_client.check_response_status(response)

    print(image_to_str(response.json()))


def create_image(client: http_client.HTTPClient,
                 name: str, display_name: str, tag: str):
    response = client.post(
        '/api/sandbox_docker_images/',
        json={
            'name': name,
            'display_name': display_name,
            'tag': tag,
        }
    )
    http_client.check_response_status(response)

    print('Image created:')
    print(image_to_str(response.json()))


def edit_image(client: http_client.HTTPClient,
               pk: int,
               display_name: Optional[str] = None,
               tag: Optional[str] = None):
    data = {}
    if display_name is not None:
        data['display_name'] = display_name

    if tag is not None:
        data['tag'] = tag

    response = client.patch(f'/api/sandbox_docker_images/{pk}/', json=data)
    http_client.check_response_status(response)

    print('Image updated:')
    print(image_to_str(response.json()))


def image_to_str(image: dict) -> str:
    return f"""{image['pk']}: {image['name']}
    display_name: {image['display_name']}
    tag: {image['tag']}"""


def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    list_parser = subparsers.add_parser(
        'list',
        help=('Shows a summary of all the sandbox '
              'Docker images and their primary keys')
    )

    detail_parser = subparsers.add_parser(
        'detail',
        help='Shows a summary about the image with the specified primary key.'
    )
    detail_parser.add_argument(
        'pk', help='The primary key of the image to show')

    create_parser = subparsers.add_parser(
        'create',
        help='Register a new image. You must be a superuser to do this.'
    )
    create_parser.add_argument(
        'name',
        help="A unique name identifying the image."
    )
    create_parser.add_argument(
        'display_name',
        help="A human-readable name shown to users on the website."
    )
    create_parser.add_argument(
        'tag',
        help=("The value of the argument you would pass to `docker pull` "
              "in order to download the image. IMPORTANT: You should include "
              "the version number in the tag and update it whenever you "
              "update the image, otherwise your tests might use a stale "
              "version of the image.")
    )

    edit_parser = subparsers.add_parser(
        'edit',
        help=('Edit the specified image metadata. '
              'You must be a superuser to do this.')
    )
    edit_parser.add_argument(
        'pk', type=int, help='The primary key of the image to edit')
    edit_parser.add_argument(
        '--display_name', '-d',
        default=None,
        help="The new value for the image's display name."
    )
    edit_parser.add_argument(
        '--tag', '-t',
        default=None,
        help=("The new value for the image's tag. "
              "The tag is the same as the argument you would "
              "pass to `docker pull`")
    )

    parser.add_argument('--base_url', '-u', type=str,
                        default='https://autograder.io/api/')
    parser.add_argument(
        '--token_file', '-t', type=str, default='.agtoken',
        help="A filename or a path describing where to find the API token. "
             "If a filename, searches the current directory and each "
             "directory up to and including the current user's home "
             "directory until the file is found.")

    return parser.parse_args()


if __name__ == '__main__':
    main()
