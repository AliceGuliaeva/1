import hashlib
import os
import pathlib
import re
import stat
import typing as tp
import zlib

from pyvcs.refs import update_ref
from pyvcs.repo import repo_find


def hash_object(data: bytes, fmt: str, write: bool = False) -> str:
    # PUT YOUR CODE HERE
    formatted_data = (fmt + f" {len(data)}\0").encode() + data
    hash_str = hashlib.sha1(formatted_data).hexdigest()
    if write:
        dir_path = repo_find(".") / "objects"
        try:
            dir_path /= hash_str[:2]
            dir_path.mkdir()
        except FileExistsError:
            pass
        with (dir_path / hash_str[2:]).open("wb") as f:
            f.write(zlib.compress(formatted_data))
    return hash_str


def resolve_object(obj_name: str, gitdir: pathlib.Path) -> tp.List[str]:
    # PUT YOUR CODE HERE
    if len(obj_name) < 4:
        raise ValueError(f"Not a valid object name {obj_name}")
    object_dir = gitdir / "objects"
    result = list(
        map(
            lambda x: "".join(str(x).split("/")[-2:]),
            filter(
                lambda x: str(x).split("/")[-1].startswith(obj_name[2:]),
                (object_dir / obj_name[:2]).glob(f"{obj_name[2:]}*"),
            ),
        )
    )
    if len(result) == 0:
        raise ValueError(f"Not a valid object name {obj_name}")
    return result


def find_object(obj_name: str, gitdir: pathlib.Path) -> str:
    # PUT YOUR CODE HERE
    dir_name = obj_name[:2]
    file_name = obj_name[2:]
    path = str(gitdir) + "/" + dir_name + "/" + file_name
    return path


def read_object(sha: str, gitdir: pathlib.Path) -> tp.Tuple[str, bytes]:
    # PUT YOUR CODE HERE
    object_dir = gitdir / "objects"
    with (object_dir / sha[:2] / sha[2:]).open("rb") as f:
        file_content = zlib.decompress(f.read())
    extra_data, main_content = file_content.split(b"\x00", maxsplit=1)
    b_fmt: bytes
    b_length: bytes
    b_fmt, b_length = extra_data.split()
    fmt = b_fmt.decode()
    length = int(b_length)
    if length != len(main_content):
        raise ValueError(f"Object {sha} is damaged")
    return fmt, main_content


def read_tree(data: bytes) -> tp.List[tp.Tuple[int, str, str]]:
    # PUT YOUR CODE HERE
    result = []
    while data:
        before_sha_ind = data.index(b"\00")
        mode, name = data[:before_sha_ind].decode().split(" ")
        sha = data[before_sha_ind + 1: before_sha_ind + 21]
        result.append((int(mode), name, sha.hex()))
        data = data[before_sha_ind + 21:]
    return result


def cat_file(obj_name: str, pretty: bool = True) -> None:
    # PUT YOUR CODE HERE
    data = read_object(obj_name, repo_find("."))
    if data[0] in ("blob", "commit"):
        out = data[1].decode()
        if pretty:
            print(out)
        else:
            print(data[0], out)
    elif data[0] == "tree":
        out1 = read_tree(data[1])
        if pretty:
            print(
                *[f'{x[0]:06} {"tree" if x[0] == 40000 else "blob"} {x[2]}\t{x[1]}' for x in out1],
                sep="\n",
            )
        else:
            print(
                data[0],
                "\n".join(
                    f'{x[0]:06} {"tree" if x[0] == 40000 else "blob"} {x[2]}\t{x[1]}' for x in out1
                ),
            )


def find_tree_files(tree_sha: str, gitdir: pathlib.Path) -> tp.List[tp.Tuple[str, str]]:
    # PUT YOUR CODE HERE
    tree_files = []
    _, tree = read_object(tree_sha, gitdir)
    tree_entries = read_tree(tree)
    for entry in tree_entries:
        pointer_type, _ = read_object(entry[1], gitdir)
        path = pathlib.Path(entry[2]).relative_to(gitdir.parent)
        if path.is_dir():
            accumulator += str(path) + "/"
        if pointer_type == "tree":
            tree_files += find_tree_files(entry[1], gitdir, accumulator)
        else:
            tree_files.append((entry[1], accumulator + str(path)))
    return tree_files


def commit_parse(raw: bytes, start: int = 0, dct=None):
    # PUT YOUR CODE HERE
    data: tp.Dict[str, tp.Any]
    data = {"message": []}
    for line in raw.decode().split("\n"):
        if line.startswith(("tree", "parent", "author", "committer")):
            name, val = line.split(" ", maxsplit=1)
            data[name] = val
        else:
            data["message"].append(line)
    return data